# auto-publish
###### 分布式发布应用程序，通过容器内的构建源码并提交到指定的服务器中他，通过不同容器环境进行构建，程序分为打包端和发布端，发布端基本一致

###### 中间件说明
- nacos配置中心
- oss阿里云文件服务存储
###### 基础环境说明
- python 3.8
###### JAVA环境说明
- maven 3.6.3
- jdk-8u241-linux-x64
###### NODE环境说明
- nodejs 12
- npm 6
###### 关于GIT-URL的说明
http://www.kernel.org/pub/software/scm/git/docs/git-clone.html#URLS
- 为了安全git只同步master分支作为编译分支
- 自动检测时间默认为60秒
- GIT仓库的根目录下需要有setting.xml的maven配置，如果使用默认配置可能会编译失败
###### 配置文件格式为yaml说明demo.package
```
#git地址
git:
    url: https://【账号】:【密码】@github.com/numen06/jar-publish.git
#服务器配置
#需要发布到的服务器地址
server:
    test1:
        ip: 192.168.8.168
        user: root
        password: root
    test2:
        ip: 192.168.8.168
        user: root
        password: root
#开始为编译目录
build:
    #编译完成之后一般都有很多个JAR包，可以分别发布
    test1:
        #选择多个服务器发布
        server:
            - test1
            - test2
        #打包完成的jar指定目录
        local: /okc-emc-auth/pom.xml
        #远程服务器放置的地址
        remote: /home/app.jar
        #编译完成之后执行命令
        #cmd: zip
        #放置完成后执行的命令
        appctl: docker restart app
    test2:
        #选择多个服务器发布
        server:
            - test1
            - test2
        #打包完成的jar指定目录
        local: /okc-emc-auth/pom.xml
        #远程服务器放置的地址
        remote: /home/app.jar
        #编译完成之后执行命令
        #cmd: zip
        #放置完成后执行的命令
        appctl: docker restart app
```
###### 简单执行
```
docker run -itd --name jar-publish -v /opt/jar-publish/demo.package:/app/demo.package registry.cn-hangzhou.aliyuncs.com/numen/jar-publish
#轮训时间设置
-e git.interval=60
#设置Maven的Setting.xml
-e maven.settings=/app/settings.xml
#编译日志文件输出目录
-v /opt/jar-publish/logs:/app/logs
```
###### 编译过程(如果想到打包自己的容器的话)
```
docker build -t registry.cn-hangzhou.aliyuncs.com/numen/jar-publish .
docker push registry.cn-hangzhou.aliyuncs.com/numen/jar-publish
```




