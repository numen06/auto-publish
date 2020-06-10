# -*- coding: UTF-8 -*-
import smtplib
import os
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart


class MailSender(object):

    def __init__(self, mailConfig):
        self.mailConfig = mailConfig

    def buildMail(self,subject,context):
        msg =  MIMEMultipart()
        msg['From'] = formataddr(["JBM自动编译器", self.mailConfig['from']])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        # msg['To'] = formataddr(["收件人", self.mailConfig['to']])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject'] = subject  # 邮件的主题，也可以说是标题
        return msg

    def sendMail(self,subject,context):
        try:
            msg= self.buildMail(subject,context)
            server = smtplib.SMTP_SSL(self.mailConfig['host'], self.mailConfig['port'])  # 发件人邮箱中的SMTP服务器，端口是25
            server.login(self.mailConfig['username'], self.mailConfig['password'])  # 括号中对应的是发件人邮箱账号、邮箱密码
            to_addrs = self.mailConfig['to'].split(',')
            server.sendmail(self.mailConfig['username'], to_addrs, msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
            server.quit()  # 关闭连接
            print("邮件发送成功")
        except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
            print("邮件发送失败")
            raise Exception

    def sendAttMail(self,subject,context,attFilePath):
        try:
            msg= self.buildMail(subject,context)
            # 构造附件1，传送当前目录下的 test.txt 文件
            att1 = MIMEText(open(attFilePath, 'rb').read(), 'base64', 'utf-8')
            att1["Content-Type"] = 'application/octet-stream'
            # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
            att1["Content-Disposition"] = 'attachment; filename="'+os.path.basename(attFilePath)+'"'
            msg.attach(att1)
            server = smtplib.SMTP_SSL(self.mailConfig['host'], self.mailConfig['port'])  # 发件人邮箱中的SMTP服务器，端口是25
            server.login(self.mailConfig['username'], self.mailConfig['password'])  # 括号中对应的是发件人邮箱账号、邮箱密码
            to_addrs = self.mailConfig['to'].split(',')
            server.sendmail(self.mailConfig['username'], to_addrs, msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
            server.quit()  # 关闭连接
            print("邮件发送成功")
        except Exception as e: # 如果 try 中的语句没有执行，则会执行下面的 ret=False
            print("邮件发送失败" ,e)
            raise Exception
