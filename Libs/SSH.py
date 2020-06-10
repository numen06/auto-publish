# -*- coding: utf-8 -*-
import paramiko
from Libs import Log

log = Log.Logger('logs/build.log', level='debug').logger

class SSH(object):
    def connect(self,ip,user,password):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(ip,user,password ,allow_agent=True)
        self.log.info("SSH链接服务器成功:%s" % ip)

    def upload(self,local_file_path,remote_file_path):
        self.log.info("开始上传文件：%s-->%s" % local_file_path+'-->'+remote_file_path)
        sftp = self.ssh.open_sftp()
        sftp.put(local_file_path, remote_file_path)
        sftp.close()
        self.log.info("结束上传文件：%s" % local_file_path+'-->'+remote_file_path)

    def exec_command(self,cmd):
        self.log.info("开始执行远程命令:%s" % cmd)
        self.log.info(self.exec_command(cmd))
        self.log.info("完成远程命令")