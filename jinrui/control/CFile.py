import oss2, os, cv2, platform, uuid, shutil

from datetime import datetime
from pptx import Presentation
from pptx.util import Inches
from flask import current_app, request

from ..extensions.success_response import SuccessCode
from ..extensions.error_response import NoQuestion, ClassNoStudent, NoAnswer, NoErrCode
from ..extensions.params_validates import parameter_required
from jinrui.models.jinrui import j_question, j_paper, j_student, j_answer_booklet, j_score
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