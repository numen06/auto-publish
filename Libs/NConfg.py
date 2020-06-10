# -*- coding: utf8 -*-
from __future__ import print_function
import unittest
import nacos
from nacos import files
import time
import shutil


class NacosClient(object):
    # get config
    # data_id = "okc.package"
    group = "DEFAULT_GROUP"

    def __init__(self,SERVER_ADDRESSES,NAMESPACE):
        # SERVER_ADDRESSES = "nacos.mumiorg.com:80"
        # NAMESPACE = "d1133b00-6399-44a8-b33d-4e33c3d4fe4e"
        print(SERVER_ADDRESSES,NAMESPACE )
        self.client = nacos.NacosClient(SERVER_ADDRESSES, namespace=NAMESPACE)

    # def NacosClient(self):
    #     return self.client;

    def get_config(self,data_id):
        print("开始读取远程配置",data_id)
        return self.client.get_config(data_id, self.group)





