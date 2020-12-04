# -*- coding: utf-8 -*-

from aliyunsdkcore import client
from aliyunsdksts.request.v20150401 import AssumeRoleRequest
import json, uuid, requests, datetime
import oss2

# Endpoint以杭州为例，其它Region请按实际情况填写。
endpoint = 'oss-cn-shanghai.aliyuncs.com'
bucket_name = 'jinrui-sheet'

response = requests.get("https://jinrui.sanbinit.cn/api/file/get_token")
content = json.loads(response.content)
print(content)
token = content["data"]

# 使用临时token中的认证信息初始化StsAuth实例。
auth = oss2.StsAuth(token['Credentials']['AccessKeyId'],
                    token['Credentials']['AccessKeySecret'],
                    token['Credentials']['SecurityToken'])

# 使用StsAuth实例初始化存储空间。
bucket = oss2.Bucket(auth, endpoint, bucket_name)

zip_uuid = str(uuid.uuid1())
object_name = "zip-" + zip_uuid + ".zip"
# 下载object。
print(datetime.datetime.now())
read_obj = bucket.put_object_from_file(object_name, "D:\\test3.zip")
print(datetime.datetime.now())
print("https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/zip-" + zip_uuid + ".zip")
print(read_obj.status)
