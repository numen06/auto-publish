# -*- coding: utf-8 -*-
import os
import git
# import paramiko
from Libs.Log import Logger
import yaml
import time
from Libs.NConfg import NacosClient
from Libs.OSS import AliOSS
from Libs.MAIL import MailSender


# self.log.logger.basicConfig(level=self.log.logger.DEBUG,format='%(asctime)s %(filename)s[line:%(lineno)d] %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
class SyncCode():
    isRuning = False
    # 工作目录
    basePath = os.getcwd()
    # 项目地址
    projectPath = "sources"
    config = None
    # 最后一次提交
    lastcommit = ''
    isError = False
    # 初始化配置中心
    log = Logger('logs/build.log', level='debug')
    # 编译批次
    # buildBatch=None
    SERVER_ADDRESSES = os.environ["NACOS_SERVER"]
    NAMESPACE = os.environ["NACOS_NAMESPACE"]
    DATA_ID = os.environ["NACOS_DATA_ID"]

    # 初始化OSS

    nconfig = NacosClient(SERVER_ADDRESSES, NAMESPACE)

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
        # self.configs.append(config)

    def autoSync(self):
        env_dist = os.environ
        interval = self.config['interval']
        # 编译时间戳
        now = int(time.time())
        timeArray = time.localtime(now)
        self.buildBatch = time.strftime("%Y-%m-%d_%H_%M", timeArray)
        # self.log = Logger('logs/build_'+self.buildBatch+'.log', level='debug')
        self.log.logger.info("开始执行自动同步,检查间隔时间为:%s秒" % interval)
        while (True):
            config = self.config

            if (self.gitClone(config)):
                self.log.logger.info("监测到代码变动")
                self.sync(config)
            if (self.isError):
                self.log.logger.info("上一次执行错误,休息10秒后继续执行")
                time.sleep(10)
                self.sync(config)
            time.sleep(interval)
            self.log.logger.info("休眠后重新刷新配置")
            self.loadConfig(self.basePath)
            self.log.logger.info("刷新配置完成")

    def gitClone(self, config):
        change = False
        try:
            if (self.isRuning):
                raise Exception("打包程序正在执行")
            gitUrl = config['git']['url']
            branch = config['git']['branch']
            self.log.logger.info("git.url:%s" % gitUrl)
            repo = {}

            # 同步代码
            if (os.path.exists(self.projectPath)):
                repo = git.Repo(self.projectPath)
                self.log.logger.info(repo.git.branch('-r'))
                beforeBranch = repo.git.branch()
                self.log.logger.info('当前分支%s' % beforeBranch)
                repo.git.checkout(branch)
                afterBranch = repo.git.branch()
                self.log.logger.info('切换后分支%s' % afterBranch)
                self.log.logger.info("开始[%s]分支的同步代码" % repo.git.branch())
                origin = repo.remotes.origin
                res = origin.fetch()
                origin.pull()
                headcommit = repo.heads.master.commit
                self.log.logger.info("更新后最后一次提交为:%s" % headcommit)
                if (headcommit == self.lastcommit):
                    change = False
                    self.log.logger.info("没有代码更新")
                else:
                    change = True
                    self.log.logger.info("有代码更新")
                self.log.logger.info("同步代码完成")
            else:
                # 第一次的话克隆
                self.log.logger.info("首次准备克隆代码")
                repo = git.Repo.clone_from(url=gitUrl, to_path=self.projectPath)
                self.log.logger.info(repo.git.branch('-r'))
                self.log.logger.info("首次克隆代码完成")
                change = True
            self.lastcommit = repo.heads.master.commit
            self.log.logger.info("设置最后一次提交为:%s" % self.lastcommit)
        except Exception as e:
            change = False
            self.log.logger.info("同步代码异常%s" % e)
        finally:
            return change

    def build(self):
        try:
            buildConfig = self.config['build']
            buildName = buildConfig['name']
            if self.config['build']['pause'] == True:
                self.log.logger.info("跳过编译")
                return False
            buildPath = os.path.join(self.basePath, self.projectPath)
            self.log.logger.info("切换工作目录准备编译:%s" % buildPath)
            os.chdir(buildPath)
            self.log.logger.info("开始%s编译", buildName)
            if 'configs' in buildConfig:
                # 如果存在前置条件
                for downloadConfig in buildConfig['configs']:
                    self.log.logger.info("开始下载前置配置文件%s", downloadConfig)
                    with open(downloadConfig, 'w') as file_object:
                        context = self.nconfig.get_config(downloadConfig)
                        file_object.write(context)
                    self.log.logger.info("保存下载前置配置文件%s", downloadConfig)
            # 编译文件
            cmd = buildConfig['cmd']
            self.log.logger.info("编译命令:%s", cmd)
            self.log.logger.info(os.system(cmd))
            self.log.logger.info("编译成功:%s", cmd)
            return True
        except Exception as e:
            self.log.logger.error("编译%s错误", buildName)
            raise e
        finally:
            self.log.logger.info("结束%s编译", buildName)

    def uploadFile(self, section, osscofig):
        try:
            # 获取文件信息
            local_file_path = os.path.normpath(os.path.join(self.basePath, self.projectPath, section['local']))
            # 获取远程分支
            remote_file_path = os.path.normpath(os.path.join(self.config['git']['branch'], os.path.basename(local_file_path)))
            self.log.logger.info("初始化OSS")

            self.log.logger.info("完成初始化OSS")
            self.log.logger.info("basePath:%s" % self.basePath)
            self.log.logger.info("projectPath:%s" % self.projectPath)
            self.log.logger.info("local:%s" % local_file_path)
            self.log.logger.info("remote:%s" % remote_file_path)
            if (os.path.exists(local_file_path) == False):
                raise Exception("未找到编译文件:%s" % local_file_path);
        except Exception as e:
            raise e;
        try:
            self.log.logger.info("开始上传至服务器")
            self.bucket.put_object_from_file(remote_file_path, local_file_path)
            self.log.logger.info("开始删除编译文件:%s" % local_file_path)
            os.remove(local_file_path)
            self.log.logger.info("完成删除编译文件")
        except Exception as e:
            self.log.logger.error("上传编译文件错误%s" % e)
            raise e

    def sync(self, config):
        try:
            if (self.isRuning):
                raise Exception("打包程序正在执行")
            self.isRuning = True
            self.log.logger.info("打包程序开始执行")
            # self.gitClone(config)
            if self.build() == True:
                self.log.logger.info("编译成功后执行发布任务")
                for sectionName in config['package']:
                    self.syncOne(config, sectionName)
            self.isError = False
        except Exception as e:
            self.isError = True
            self.log.logger.error("打包过程中发生错误:%s" % e)
        finally:
            # 编译结束发送邮件
            self.sendBuildMail()
            self.log.logger.info("打包程序完成")
            self.isRuning = False

    def syncOne(self, config, sectionName):
        try:
            self.log.logger.info("查找到发布配置:%s" % sectionName)
            section = config['package'][sectionName]
            print(section)
            # 需要上传的服务地址
            # for serverName in section['server']:
            #     # server = config['server'][serverName]
            oss = config['oss']
            self.uploadFile(section, oss)
            # 如果正常则删除错误信息
        except Exception as e:
            # 如果错误把错误信息放进去
            self.log.logger.error("发布错误:%s" % e)
            raise e

    def sendBuildMail(self):
        try:
            # 切换回根目录
            os.chdir(self.basePath)
            # 恢复日志输出
            logName = os.path.abspath(self.log.filename)
            subject = ''
            if (self.isError):
                subject = self.config['build']['name'] + self.buildBatch + '编译失败'
            else:
                subject = self.config['build']['name'] + self.buildBatch + '编译成功'

            self.mailSender.sendAttMail(subject, subject, logName)

        except Exception:
            raise Exception
        finally:
            # 删除日志
            self.log.remove()


# 开始执行方法
syncCode = SyncCode()
syncCode.autoSync()
