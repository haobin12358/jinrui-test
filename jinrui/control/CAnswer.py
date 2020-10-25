# -*- coding: utf-8 -*-
import os, uuid, oss2, shutil, platform, zipfile, json
from datetime import datetime

from ..config.enums import TestEnum
from ..extensions.success_response import Success
from jinrui.config.secret import ACCESS_KEY_SECRET, ACCESS_KEY_ID, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME
from jinrui.extensions.register_ext import db
from ..extensions.params_validates import parameter_required
from jinrui.extensions.error_response import ErrorFileType, ErrorAnswerType
from jinrui.models.jinrui import j_question, j_answer_zip, j_answer_pdf, j_paper, j_answer_sheet
from flask import current_app

class CAnswer():

    def upload_booklet(self):

        data = parameter_required(("paperId", "type", "url"))

        zip_name = data.get("url").split("/")[-1]
        if zip_name.split(".")[-1] != "zip":
            return ErrorFileType("请上传zip类型文件")
        if data.get("type") not in ["0", "1"]:
            return ErrorAnswerType("请研发检查传递值...")

        zip_uuid = str(uuid.uuid1())
        # 将zip存储进表，防止解析失败或者趸机
        with db.auto_commit():
            zip_dict = {
                "isdelete": 0,
                "createtime": datetime.now(),
                "updatetime": datetime.now(),
                "zip_id": zip_uuid,
                "zip_url": data.get("url"),
                "zip_upload_user": "system",
                "zip_status": "300101"
            }
            zip_instance = j_answer_zip.create(zip_dict)
            db.session.add(zip_instance)

        # 创建zip存储路径
        if platform.system() == "Windows":
            zip_path = "D:\\jinrui_zip\\" + zip_uuid + "\\"
        else:
            zip_path = "/tmp/jinrui_zip/" + zip_uuid + "/"
        if not os.path.exists(zip_path):
            os.makedirs(zip_path)

        auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)

        zip_name = data.get("url").split("/")
        zip_save_path = zip_path + zip_name[-1]
        # 存储zip到本地
        bucket.get_object_to_file(zip_name[-1], zip_save_path)

        zip_file = zipfile.ZipFile(zip_save_path)
        if os.path.isdir(zip_save_path + "_files"):
            pass
        else:
            os.mkdir(zip_save_path + "_files")
        for names in zip_file.namelist():
            zip_file.extract(names, zip_save_path + "_files/")
        zip_file.close()

        paper = j_paper.query.filter(j_paper.name == data.get("paperId"), j_paper.type == "A").first_("未找到该试卷")
        sheet_id = paper.sheet_id
        sheet = j_answer_sheet.query.filter(j_answer_sheet.id == sheet_id).first_("未找到答题卡")
        # 获取pdf文件列表
        pdf_file = zip_save_path + "_files"
        pdfs = os.listdir(pdf_file)
        with db.auto_commit():
            # 遍历提交pdf到数据库
            for pdf in pdfs:
                if os.path.splitext(pdf)[1] == '.pdf':
                    pdf_uuid = str(uuid.uuid1())
                    pdf_path, pdf_fullname = os.path.split(pdf)
                    pdf_name, pdf_ext = os.path.splitext(pdf_fullname)
                    pdf_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" \
                              + pdf_name + "-" + pdf_uuid + "." + pdf_ext
                    result = bucket.put_object_from_file(pdf_name + "-" + pdf_uuid + "." + pdf_ext,
                                                         os.path.join(pdf_file, pdf))
                    current_app.logger.info(">>>>>>>>>>>>result:" + str(result.status))

                    if data.get("type") == "0":
                        pdf_use = "300201"
                    else:
                        pdf_use = "300202"

                    pdf_dict = {
                        "isdelete": 0,
                        "createtime": datetime.now(),
                        "updatetime": datetime.now(),
                        "pdf_id": pdf_uuid,
                        "zip_id": zip_uuid,
                        "pdf_use": pdf_use,
                        "paper_name": data.get("paperId"),
                        "sheet_dict": sheet.json,
                        "pdf_status": "300301",
                        "pdf_url": pdf_url,
                        "pdf_address": "zip"
                    }

                    pdf_instance = j_answer_pdf.create(pdf_dict)
                    db.session.add(pdf_instance)

            zip_file = j_answer_zip.query.filter(j_answer_zip.zip_id == zip_uuid).first()
            zip_instance = zip_file.update({
                "zip_status": "300102"
            }, null="not")
            db.session.add(zip_instance)

        shutil.rmtree(zip_path)
        return {
            "code": 200,
            "success": True,
            "message": "上传成功"
        }