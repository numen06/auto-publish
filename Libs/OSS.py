# -*- coding: utf-8 -*-
import oss2
from Libs import Log


class AliOSS(object):
    log = Log.Logger('logs/oss.log', level='debug').logger
    endpoint = 'https://oss-accelerate.aliyuncs.com'  # Suppose that your bucket is in the Hangzhou region.
    def __init__(self, osscofig):
        access_key_id = osscofig['access_key_id']
        access_key_secret = osscofig['access_key_secret']
        bucket = osscofig['bucket']
        self.log.info("access_key_id:%s,access_key_secret:%s,bucket:%s"% (access_key_id, access_key_secret,bucket))
        auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(auth, self.endpoint, bucket)

    def def_bucket(self):
        return self.bucket
