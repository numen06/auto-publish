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
###### 配置文件格式说明查看文档
- demo.package
- demo.publish
###### Docker运行编译程序
```
docker run -itd --privileged=true --restart=always --name jar-build -e NACOS_SERVER=【你的服务器地址】 -e NACOS_NAMESPACE=【你的命名空间】 -e NACOS_DATA_ID=【你的编译配置文件.package】 registry.cn-hangzhou.aliyuncs.com/numen/auto-publish:【node/maven】
```
###### Docker运行发布程序
```
docker run -itd --privileged=true --restart=always --name jar-build -e NACOS_SERVER=【你的服务器地址】 -e NACOS_NAMESPACE=【你的命名空间】 -e NACOS_DATA_ID=【你的编译配置文件.publish】 registry.cn-hangzhou.aliyuncs.com/numen/auto-publish:latest
```




