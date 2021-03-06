# -*- coding: utf-8 -*-
import os, uuid, oss2, shutil, platform, zipfile, json
from datetime import datetime

from ..config.enums import PngType
from ..extensions.success_response import Success
from jinrui.config.secret import ACCESS_KEY_SECRET, ACCESS_KEY_ID, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME
from jinrui.extensions.register_ext import db, ali_oss
from ..extensions.params_validates import parameter_required
from jinrui.extensions.error_response import ErrorFileType, ErrorAnswerType, ParamsError
from jinrui.models.jinrui import j_manager, j_answer_zip, j_answer_pdf, j_paper, j_answer_sheet, j_answer_png, \
    j_role, j_organization, j_school_network, j_answer_upload, j_score, j_answer_booklet
from flask import current_app, request
from sqlalchemy import false

class CAnswer():

    def upload_booklet(self):

        data = parameter_required(("paperId", "type", "url", "id"))

        zip_name = data.get("url").split("/")[-1]
        if zip_name.split(".")[-1] != "zip":
            return ErrorFileType("请上传zip类型文件")
        if data.get("type") not in ["0", "1"]:
            return ErrorAnswerType("请研发检查传递值...")

        manager = j_manager.query.filter(j_manager.id == data.get("id")).first_("未找到该用户")

        pdf_ip = request.remote_addr

        if data.get("type") == "0":
            zip_use = "300201"
        else:
            zip_use = "300202"
        zip_uuid = str(uuid.uuid1())
        # 将zip存储进表，防止解析失败或者趸机
        with db.auto_commit():
            zip_dict = {
                "isdelete": 0,
                "createtime": datetime.now(),
                "updatetime": datetime.now(),
                "zip_id": zip_uuid,
                "zip_url": data.get("url"),
                "zip_upload_user": manager.name,
                "zip_status": "300101",
                "zip_ip": pdf_ip,
                "zip_paper": data.get("paperId"),
                "zip_use": zip_use,
                "zip_upload_userid": data.get("id")
            }
            zip_instance = j_answer_zip.create(zip_dict)
            db.session.add(zip_instance)
        return {
            "code": 200,
            "success": True,
            "message": "上传成功"
        }

    def delete_upload(self):
        """
        逻辑删除答卷
        """
        args = parameter_required(("id", "user_id"))
        user_id = args.get("user_id")
        upload_id = args.get("id")

        user = j_role.query.filter(j_role.manager_id == user_id).first()
        if user.role_type != "SUPER_ADMIN":
            return {
                "code": 405,
                "success": False,
                "message": "无权限"
            }
        upload = j_answer_upload.query.filter(j_answer_upload.id == upload_id).first()
        with db.auto_commit():
            upload_instance = upload.update({
                "is_delete": 1
            }, null="not")
            db.session.add(upload_instance)

        return {
            "code": 200,
            "success": True,
            "message": "删除成功"
        }

    def deal_zip(self):
        zip_dict = j_answer_zip.query.filter(j_answer_zip.isdelete == 0, j_answer_zip.zip_status == "300101")\
            .order_by(j_answer_zip.createtime.desc()).first()
        if zip_dict:
            zip_uuid = zip_dict.zip_id
            # 创建zip存储路径
            if platform.system() == "Windows":
                zip_path = "D:\\jinrui_zip\\" + zip_uuid + "\\"
            else:
                zip_path = "/tmp/jinrui_zip/" + zip_uuid + "/"
            if not os.path.exists(zip_path):
                os.makedirs(zip_path)

            auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
            bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)

            zip_name = zip_dict.zip_url.split("/")
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

            paper = j_paper.query.filter(j_paper.name == zip_dict.zip_paper, j_paper.type == "A").first_("未找到该试卷")
            sheet_id = paper.sheet_id
            sheet = j_answer_sheet.query.filter(j_answer_sheet.id == sheet_id).first_("未找到答题卡")
            # 获取pdf文件列表
            pdf_file = zip_save_path + "_files"
            pdfs = os.listdir(pdf_file)
            upload_id = str(uuid.uuid1())

            school_network = j_school_network.query.filter(j_school_network.net_ip == zip_dict.zip_ip).first()
            if school_network:
                school_name = school_network.school_name
            else:
                school_name = None

            with db.auto_commit():
                # 遍历提交pdf到数据库
                for pdf in pdfs:
                    if os.path.splitext(pdf)[1] == '.pdf':
                        pdf_uuid = str(uuid.uuid1())
                        pdf_path, pdf_fullname = os.path.split(pdf)
                        pdf_name, pdf_ext = os.path.splitext(pdf_fullname)
                        pdf_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" \
                                  + "pdf-" + pdf_uuid + "." + pdf_ext
                        result = bucket.put_object_from_file("pdf-" + pdf_uuid + "." + pdf_ext,
                                                             os.path.join(pdf_file, pdf))
                        current_app.logger.info(">>>>>>>>>>>>result:" + str(result.status))

                        pdf_use = zip_dict.zip_use

                        pdf_dict = {
                            "isdelete": 0,
                            "createtime": datetime.now(),
                            "updatetime": datetime.now(),
                            "pdf_id": pdf_uuid,
                            "zip_id": zip_uuid,
                            "pdf_use": pdf_use,
                            "paper_name": zip_dict.zip_paper,
                            "sheet_dict": sheet.json,
                            "pdf_status": "300305",
                            "pdf_url": pdf_url,
                            "pdf_address": "zip",
                            "pdf_school": school_name,
                            "pdf_ip": zip_dict.zip_ip,
                            "upload_id": upload_id
                        }

                        pdf_instance = j_answer_pdf.create(pdf_dict)
                        db.session.add(pdf_instance)
                    else:
                        # 将zip状态改为非法
                        zip_file = j_answer_zip.query.filter(j_answer_zip.zip_id == zip_uuid).first()
                        zip_instance = zip_file.update({
                            "zip_status": "300104"
                        }, null="not")
                        db.session.add(zip_instance)
                        # TODO 将ip拉入黑名单

                        # 删除oss上的zip
                        auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                        bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                        result = bucket.delete_object(zip_name[-1])
                        current_app.logger.info(">>>>>>>>>>>>>>>>>>>>>>delete_oss:" + str(result.status))
                        current_app.logger.info(">>>>>>>>>>>>>>>>>>>>>>delete_zip_name:" + str(zip_name[-1]))

                        raise Exception("存在非法zip,已将ip：{0}拉入黑名单")

                zip_file = j_answer_zip.query.filter(j_answer_zip.zip_id == zip_uuid).first()
                zip_instance = zip_file.update({
                    "zip_status": "300102"
                }, null="not")
                db.session.add(zip_instance)

                user_id = zip_dict.zip_upload_userid
                orgid_list = []
                roletype_list = []
                roles = j_role.query.filter(j_role.manager_id == user_id).all()
                if roles:
                    for role in roles:
                        if role.role_type not in roletype_list:
                            roletype_list.append(role.role_type)
                        if role.org_id not in orgid_list:
                            orgid_list.append(role.org_id)

                class_id = json.dumps([])
                if "TEACHER" in roletype_list or "CLASS" in roletype_list:
                    class_id = json.dumps(orgid_list)

                grade_id = None
                if "GRADE" in roletype_list:
                    if orgid_list:
                        grade_id = orgid_list[0]

                school_id = None
                if "SCHOOL" in roletype_list or "SCHOOL_ADMIN" in roletype_list:
                    if orgid_list:
                        school_id = orgid_list[0]

                upload_dict = {
                    "is_delete": 0,
                    "create_time": datetime.now(),
                    "update_time": datetime.now(),
                    "id": upload_id,
                    "upload_by": zip_dict.zip_upload_user,
                    "status": "处理中",
                    "url": zip_dict.zip_url,
                    "upload_byid": user_id,
                    "school_id": school_id,
                    "school_name": None,
                    "grade_id": grade_id,
                    "grade_name": None,
                    "class_id": class_id,
                    "class_name": None
                }
                upload_instance = j_answer_upload.create(upload_dict)
                db.session.add(upload_instance)

            # 删除oss上的zip
            auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
            bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
            result = bucket.delete_object(zip_name[-1])
            current_app.logger.info(">>>>>>>>>>>>>>>>>>>>>>delete_oss:" + str(result.status))
            current_app.logger.info(">>>>>>>>>>>>>>>>>>>>>>delete_zip_name:" + str(zip_name[-1]))

            shutil.rmtree(zip_path)
        else:
            current_app.logger.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>get_zip:0")

    def get_answer_list(self):

        args = parameter_required(("png_status", ))

        filter_args = [j_answer_png.isdelete == 0]
        filter_args.append(j_answer_png.png_type.in_(["21", "22", "23", "25", "27"]))
        if args.get("png_status") == "待处理":
            filter_args.append(j_answer_png.png_status == "303")
        elif args.get("png_status") == "已处理":
            filter_args.append(j_answer_png.png_status == "302")
        elif args.get("png_status") == "已批阅":
            filter_args.append(j_answer_png.png_status == "301")
        else:
            return {
                "code": 405,
                "success": False,
                "message": "错误的状态"
            }

        if args.get("school"):
            filter_args.append(j_answer_png.school.like("%{0}%".format(args.get("school"))))
        if args.get("student_no"):
            filter_args.append(j_answer_png.student_no.like("%{0}%".format(args.get("student_no"))))
        answer_list = j_answer_png.query.filter(*filter_args).all_with_page()
        for answer in answer_list:
            answer.fill("png_type_ch", PngType(int(answer.png_type)).zh_value)
            if answer.png_status == "301":
                answer.png_status = "已批阅"
            elif answer.png_status == "302":
                answer.png_status = "已处理"
            elif answer.png_status == "303":
                answer.png_status = "待处理"
            else:
                answer.png_status = "未知状态"
            answer.createtime = answer.createtime.strftime("%Y-%m-%d %H:%M")
        all_answer = j_answer_png.query.filter(*filter_args).all()

        total = len(all_answer)
        size = args.get("pageSize") or 15

        if total % int(size) == 0:
            if total == 0:
                pages = 1
            else:
                pages = total / int(size)
        else:
            pages = int(total / int(size)) + 1

        return {
            "code": 200,
            "success": True,
            "message": "获取成功",
            "data": answer_list,
            "pages": pages,
            "total": total
        }

    def update_score(self):

        data = parameter_required(("png_id", "result_update"))

        with db.auto_commit():
            answer_png = j_answer_png.query.filter(j_answer_png.png_id == data.get("png_id")).first_("未找到该记录")
            current_app.logger.info(">>>>>>>>>>>>>>>>>>>png:" + str(answer_png))
            score_id = answer_png.score_id
            answer_instance = answer_png.update({
                "updatetime": datetime.now(),
                "result_update": int(data.get("result_update")),
                "png_status": "302"
            }, null="not")

            db.session.add(answer_instance)
            score = j_score.query.filter(j_score.id == score_id).first()
            score_instance = score.update({
                "status": "304",
                "score": int(data.get("result_update"))
            }, null="not")

            db.session.add(score_instance)

        with db.auto_commit():
            booklet_id = score.booklet_id
            scores_error = j_score.query.filter(j_score.booklet_id == booklet_id, j_score.status.in_(["303", "302"])).all()
            if not scores_error:
                scores = j_score.query.filter(j_score.booklet_id == booklet_id).all()
                score_end = 0
                for score in scores:
                    score_end = score_end + int(score.score)
                booklet_dict = j_answer_booklet.query.filter(j_answer_booklet.id == booklet_id).first()
                booklet_instance = booklet_dict.update({
                    "status": "4",
                    "score": score_end,
                    "grade_time": datetime.now().date()
                }, null="not")
                db.session.add(booklet_instance)



        return {
            "code": 200,
            "success": True,
            "message": "订正分数成功"
        }
