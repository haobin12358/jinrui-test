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
    j_role, j_organization, j_school_network, j_answer_upload
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
        school_network = j_school_network.query.filter(j_school_network.net_ip == pdf_ip).first()
        if school_network:
            school_name = school_network.school_name
        else:
            school_name = None

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
        upload_id = str(uuid.uuid1())
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
                        "pdf_address": "zip",
                        "pdf_school": school_name,
                        "pdf_ip": request.remote_addr,
                        "upload_id": upload_id
                    }

                    pdf_instance = j_answer_pdf.create(pdf_dict)
                    db.session.add(pdf_instance)

            zip_file = j_answer_zip.query.filter(j_answer_zip.zip_id == zip_uuid).first()
            zip_instance = zip_file.update({
                "zip_status": "300102"
            }, null="not")
            db.session.add(zip_instance)

            upload_dict = {
                "is_delete": 0,
                "create_time": datetime.now(),
                "update_time": datetime.now(),
                "id": upload_id,
                "upload_by": manager.name,
                "status": "处理中",
                "url": data.get("url")
            }
            upload_instance = j_answer_upload.create(upload_dict)
            db.session.add(upload_instance)

        shutil.rmtree(zip_path)
        return {
            "code": 200,
            "success": True,
            "message": "上传成功"
        }

    def get_answer_list(self):

        args = parameter_required(("png_status", ))

        filter_args = [j_answer_png.isdelete == 0]
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
        all_answer = j_answer_png.query.filter(*filter_args).all()

        total = len(all_answer)
        size = args.get("size") or 15

        if total % size == 0:
            if total == 0:
                pages = 1
            else:
                pages = total / size
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
            answer_png = j_answer_png.query.filter(j_answer_png.png_id == data.get("png_id")).first_("为找到该记录")

            answer_instance = answer_png.update({
                "updatetime": datetime.now(),
                "result_update": int(data.get("result_update")),
                "png_status": "302"
            }, null="not")

            db.session.add(answer_instance)

        # TODO 更新考卷情况

        return {
            "code": 200,
            "success": True,
            "message": "订正分数成功"
        }

    def upload_pdf(self):
        file = request.files.get('file')
        if not file:
            raise ParamsError('文件缺失')
        data = parameter_required()
        pdf_ip = request.remote_addr
        pdf_use = data.get('pdfuse')
        pdf_address = data.get('pdfaddress')
        pager_name = data.get('pagername')
        j_answer_pdf.query.filter(
            j_answer_pdf.pdf_ip == pdf_ip, j_answer_pdf.pdf_use == pdf_use,
            j_answer_pdf.pdf_address == pdf_address, j_answer_pdf.isdelete == false()).all()
        if j_answer_pdf:
            raise ParamsError('该pdf已上传')
        school = j_school_network.query.filter(
            j_school_network.net_ip == pdf_ip, j_school_network.isdelete == false()).first_('ip 非法，请联系管理员')
        pdf_school = school.school_name
        if not pdf_school:
            raise ParamsError('学校名丢失，请联系管理员处理')
        # todo  获取j_paper 的key
        sheet_dict_model = j_answer_sheet.query.join(j_paper, j_paper.sheet_id == j_answer_sheet.id).filter(
            j_paper.name == pager_name).first_('试卷已删除')
        sheet_dict = sheet_dict_model.json
        pdf_status = '300301'
        filename = file.filename
        shuffix = os.path.splitext(filename)[-1]
        current_app.logger.info(">>>  Upload File Shuffix is {0}  <<<".format(shuffix))
        shuffix = shuffix.lower()
        if shuffix != '.pdf':
            raise ParamsError('上传文件需要是pdf')

        img_name = self.random_name(shuffix)
        time_now = datetime.now()
        year = str(time_now.year)
        month = str(time_now.month)
        day = str(time_now.day)
        newPath = os.path.join(current_app.config['BASEDIR'], 'img', 'pdf', year, month, day)
        if not os.path.isdir(newPath):
            os.makedirs(newPath)
        newFile = os.path.join(newPath, img_name)
        # 服务器本地保存
        file.save(newFile)
        data = '/img/{folder}/{year}/{month}/{day}/{img_name}'.format(
            folder='pdf', year=year,month=month, day=day, img_name=img_name)
        # 上传oss
        self._upload_to_oss(newFile, data[1:], 'pdf')
        oss_area = 'https://jinrui.sanbinit.cn'
        pdf_url = oss_area + data
        with db.auto_commit():
            answer_pdf = j_answer_pdf.create({
                'pdf_id': str(uuid.uuid4()),
                'pdf_user': pdf_use,
                'paper_name': pager_name,
                'sheet_dict': sheet_dict,
                'pdf_status': pdf_status,
                'pdf_url': pdf_url,
                'pdf_address': pdf_address,
                'pdf_ip': pdf_ip,
                'pdf_school': pdf_school
            })
            db.session.add(answer_pdf)
        return Success('上传成功')

    def get_pdf_list(self):
        pass


    @staticmethod
    def random_name(shuffix):
        import string, random
        myStr = string.ascii_letters + '12345678'
        res = ''.join(random.choice(myStr) for _ in range(20)) + shuffix
        return res

    def _upload_to_oss(self, file_data,data, msg):

        if current_app.config.get('IMG_TO_OSS'):
            try:
                ali_oss.save(data=file_data, filename=data[1:])
            except Exception as e:
                current_app.logger.error(">>> {} 上传到OSS出错 : {}  <<<".format(msg, e))
                raise Exception('服务器繁忙，请稍后再试')
