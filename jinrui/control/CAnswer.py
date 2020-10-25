import os, uuid, oss2, shutil
from datetime import datetime

from ..config.enums import TestEnum
from ..extensions.success_response import Success
from jinrui.config.secret import ACCESS_KEY_SECRET, ACCESS_KEY_ID, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME
from jinrui.extensions.register_ext import db
from ..extensions.params_validates import parameter_required
from jinrui.models.jinrui import j_question
from flask import current_app

class CAnswer():

    def upload_booklet(self):

        return {
            "code": 200,
            "success": True,
            "message": "上传成功"
        }