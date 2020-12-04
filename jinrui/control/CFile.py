import oss2, os, cv2, platform, uuid, shutil, hashlib

from flask import current_app, request

from ..extensions.params_validates import parameter_required
from jinrui.config.secret import ACCESS_KEY_ID, ACCESS_KEY_SECRET, ALIOSS_BUCKET_NAME, ALIOSS_ENDPOINT

class CFile():

    def upload_files(self):

        file = request.files.get("file")
        if not file:
            return {
                "code": 405,
                "success": False,
                "message": "未发现文件"
            }
        filename = file.filename
        etx = os.path.splitext(filename)[-1]
        # 阿里云oss参数
        auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)

        file_uuid = str(uuid.uuid1())
        file_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + "file-" + file_uuid + etx
        result = bucket.put_object("file-" + file_uuid + etx, file)
        if result.status != 200:
            return {
                "code": 405,
                "success": False,
                "message": "阿里云oss错误"
            }
        current_app.logger.info(">>>>>>>>>>>>>>>>>>>oss_status:" + str(result))

        return {
            "code": 200,
            "success": True,
            "message": "上传成功",
            "data": {
                "url": file_url
            }
        }

    def get_token(self):
        # args = parameter_required(("id", ))
        from aliyunsdkcore import client
        from aliyunsdksts.request.v20150401 import AssumeRoleRequest
        import json
        # 阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维，请登录RAM控制台创建RAM账号。
        # role_arn为角色的资源名称。
        from jinrui.config.secret import ACCESS_KEY_ID_STS, ACCESS_KEY_SECRET_STS, ACCESS_KEY_ROLE_ARN
        # 创建policy_text。
        # 仅允许对名称为test-bucket1的Bucket下的所有资源执行GetObject操作。
        policy_text = """
        {
            "Version": "1", 
            "Statement": [
                {
                    "Action": ["sts:AssumeRole"], 
                    "Effect": "Allow", 
                    "Resource": "*"
                },
                {
                    "Action": "oss:*",
                    "Effect": "Allow",
                    "Resource": "*"
                }
            ]
        }
        """
        clt = client.AcsClient(ACCESS_KEY_ID_STS, ACCESS_KEY_SECRET_STS, 'cn-hangzhou')
        req = AssumeRoleRequest.AssumeRoleRequest()

        # 设置返回值格式为JSON。
        req.set_accept_format('json')
        req.set_RoleArn(ACCESS_KEY_ROLE_ARN)
        req.set_RoleSessionName('session-name')
        req.set_Policy(policy_text)
        body = clt.do_action_with_exception(req)

        # 使用RAM账号的AccessKeyId和AccessKeySecret向STS申请临时token。
        token = json.loads(oss2.to_unicode(body))

        return {
            "code": 200,
            "success": True,
            "message": "获取成功",
            "data": token
        }

    def get_oss_secret(self):

        args = parameter_required(("token", ))
        from jinrui.extensions.request_handler import token_to_user_
        user_dict = token_to_user_(args.get("token"))
        print(user_dict)

        # TODO 封禁ip
        # TODO 获取黑名单ip