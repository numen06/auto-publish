# -*- coding: utf-8 -*-
import os
# import git
import paramiko
from Lib.Log import Logger
import yaml
import time
from Lib.NConfg import NacosClient
from Lib.OSS import AliOSS
from Lib.MAIL import MailSender


class SyncPackage():
    isRuning = False
    # 工作目录
    basePath = os.getcwd()

    downloadDir = os.path.join(basePath, 'sources')

    if not os.path.exists(downloadDir):
        os.makedirs(downloadDir)
    # buildBatch=None
    SERVER_ADDRESSES = os.environ["NACOS_SERVER"]
    NAMESPACE = os.environ["NACOS_NAMESPACE"]
    DATA_ID = os.environ["NACOS_DATA_ID"]

    nconfig = NacosClient(SERVER_ADDRESSES, NAMESPACE)
    log = Logger('logs/publish.log', level='debug')

    errorConfigs={}
    isError = False

    def __init__(self):
        self.loadConfig(self.basePath)
    def loadConfig(self, basePath):
        self.log.logger.info("切换工作目录:%s" % self.basePath)
        if (os.path.exists(basePath) == False):
            os.makedirs(basePath);
        # 工作目录
        os.chdir(basePath)
        # 远程配置文件
        tempfile = self.nconfig.get_config(self.DATA_ID)
        self.config = yaml.safe_load(tempfile)
        self.log.logger.info(self.config)
        self.log.logger.info("配置加载完成开始初始化")
        self.mailSender = MailSender(self.config["mail"])
        self.bucket = AliOSS(self.config["oss"]).def_bucket()

    def autoSync(self):
        env_dist = os.environ
        interval = self.config['interval']
        # 发布时间戳
        now = int(time.time())
        timeArray = time.localtime(now)
        self.buildBatch = time.strftime("%Y-%m-%d_%H_%M", timeArray)
        # self.log = Logger('logs/build_'+self.buildBatch+'.log', level='debug')
        self.log.logger.info("开始执行自动同步,检查间隔时间为:%s秒" % interval)
        while (True):
            config = self.config
            try:
                self.packages(config)
            except Exception as e:
                self.isError = True
                self.log.logger.error("同步程序包错误")

            if (self.isError):
                self.log.logger.info("上一次执行错误,休息10秒后继续执行")
                time.sleep(10)
                for appName in self.errorConfigs:
                    try:
                        self.log.logger.info("开始执行错误的配置%s" % appName)
                        self.sync(config, self.errorConfigs[appName])
                    except:
                        continue

            time.sleep(interval)
            self.log.logger.info("休眠后重新刷新配置")
            self.loadConfig(self.basePath)
            self.log.logger.info("刷新配置完成")

    def packages(self, config):
        try:
            if (self.isRuning):
                raise Exception("发布程序正在执行")
            self.isRuning = True
            for appName in self.config['apps']:
                do = False
                self.log.logger.info("开始发布[%s]", appName)
                app = self.config['apps'][appName]
                package = app['package']
                path = app['path']
                cmd = app['cmd']
                servers = app['servers']
                filepath = os.path.abspath(os.path.join(self.downloadDir, package))
                fileDir= os.path.dirname(filepath)
                self.log.logger.info("文件地址:%s" %filepath)
                self.log.logger.info("文件夹地址:%s" %fileDir)
                if not os.path.exists(fileDir):
                    os.makedirs(fileDir)
                if (False == os.path.exists(filepath)):
                    # 从远程下载
                    self.log.logger.info("开始下载OSS文件:%s" % package)
                    self.bucket.get_object_to_file(package, filepath)
                    self.log.logger.info("下载完成:%s" % package)
                    do = True

                # 获取本地文件的最后修改时间
                file_last_modified = os.path.getatime(filepath)
                # 获取远程包信息
                remote_last_modified = self.bucket.get_object_meta(app['package']).last_modified
                # 如果远程文件的更新时间较新
                if (remote_last_modified > file_last_modified):
                    # 重新下载更新
                    self.log.logger.info("开始下载OSS文件:%s" % package)
                    self.bucket.get_object_to_file(package, filepath)
                    self.log.logger.info("下载完成:%s" % package)
                    do = True
                if (do):
                    # 将临时文件地址给到配置
                    app['temp'] = filepath
                    app['name'] = appName
                    # 如果程序包发生变动调取同步功能
                    self.sync(config, app)
                else:
                    self.log.logger.info("无需发布:%s" % filepath)
        except Exception as e:
            self.log.logger.info("程序包异常%s" % e)
        finally:
            self.isRuning = False
            if(do):
                self.sendBuildMail()

    def sync(self, config, appConfig):
        servers = appConfig['servers']
        for serverName in servers:
            try:
                self.log.logger.info("开始部署服务器:%s" % serverName)
                # 获取服务器配置信息
                server = config['server'][serverName]
                self.uploadFile(appConfig, server)
                if appConfig['name'] in self.errorConfigs:
                    self.errorConfigs.pop(appConfig['name'])
            except Exception as e:
                self.isError = True
                self.errorConfigs[appConfig['name']] = appConfig
                self.log.logger.info("部署服务器错误:%s" % serverName)

    def uploadFile(self, section, server):
        try:
            # 获取文件信息
            local_file_path = section['temp']
            remote_file_path = section['path']
            self.log.logger.info("local:%s" % local_file_path)
            self.log.logger.info("remote:%s" % remote_file_path)
            if (os.path.exists(local_file_path) == False):
                raise Exception("未找到编译文件:%s" % local_file_path);
        except Exception:
            raise Exception("打包编译文件错误");
        try:
            # 开始连接ssh
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(server['ip'], username=server['user'], password=server['password'], allow_agent=True)
            # 上传文件到远程机
            self.log.logger.info("开始上传文件到服务器:%s" % server['ip'])
            sftp = ssh.open_sftp()
            sftp.put(local_file_path, remote_file_path)
            sftp.close()
            self.log.logger.info("结束上传文件")
            cmd = section['cmd'].strip()
            if (cmd.isspace() == False):
                self.log.logger.info("开始执行远程命令:%s" % cmd)
                self.log.logger.info(ssh.exec_command(cmd))
                self.log.logger.info("完成远程命令")
        except Exception:
            raise
    def sendBuildMail(self):
        try:
            #切换回根目录
            os.chdir(self.basePath)
            #恢复日志输出
            logName =os.path.abspath(self.log.filename)
            subject = ''
            if(self.isError):
                subject = self.config['projectName'] + self.buildBatch + '发布失败'
            else:
                subject = self.config['projectName'] + self.buildBatch + '发布成功'
            self.mailSender.sendAttMail(subject,subject,logName)

        except Exception:
            raise Exception
        finally:
            # 删除日志
            self.log.remove()

# 开始执行方法
syncCode = SyncPackage()
syncCode.autoSync()
