import os, uuid, oss2, shutil, json, cv2, fitz, platform, requests, re
from datetime import datetime

from ..extensions.success_response import Success
from jinrui.config.secret import ACCESS_KEY_SECRET, ACCESS_KEY_ID, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME
from jinrui.extensions.register_ext import db
from ..extensions.params_validates import parameter_required
from jinrui.models.jinrui import j_question, j_answer_pdf, j_answer_png, j_student, j_organization, j_school_network, \
    j_answer_zip, j_paper, j_score, j_answer_booklet, j_answer_upload, j_answer_sheet
from flask import current_app

class COcr():

    def __init__(self):
        self.index_h = 1684 / 1124.52
        self.index_w = 1191 / 810.81
        self.width_less = 0
        self.height_less = 0
        self.jpg_list = []

    def mock_ocr_response(self):
        data = parameter_required(("image_url", "image_dict"))
        model = "/opt/jinrui/jinrui/jinrui/libsheet/models/"
        import sheet
        d = sheet.Detector(model)
        current_app.logger.info(str(d))
        pic_uuid = str(uuid.uuid1())
        pic_path = "/tmp/jinrui_pic/" + pic_uuid + "/"
        if not os.path.exists(pic_path):
            os.makedirs(pic_path)

        # 阿里云oss参数
        auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
        row_dict = data.get("image_url").split("/")
        pic_save_path = pic_path + row_dict[-1]
        bucket.get_object_to_file(row_dict[-1], pic_save_path)
        current_app.logger.info(data.get("image_dict"))
        data = d.detct_sheet(img_path=pic_save_path, json_dict=data.get("image_dict"))
        current_app.logger.info(pic_save_path)
        current_app.logger.info(data)

        shutil.rmtree(pic_path)
        return Success(data=data)

    def _use_ocr(self, image_path, image_dict):
        model = "/opt/jinrui/jinrui/jinrui/libsheet/models/"
        import sheet
        d = sheet.Detector(model)
        data = d.detct_sheet(img_path=image_path, json_dict=image_dict)
        return json.loads(data)

    def deal_pdf(self):
        # 比对正确答案处理分数
        # 处理异常情况（异常试卷和异常返回值）
        # 整体流程测试
        pdf = j_answer_pdf.query.filter(j_answer_pdf.isdelete == 0, j_answer_pdf.pdf_status == "300301")\
            .order_by(j_answer_pdf.createtime.desc()).first()
        if pdf and pdf.pdf_ip:
            school_network = j_school_network.query.filter(j_school_network.net_ip == pdf.pdf_ip).first()
            if school_network:
                school_name = school_network.school_name
            else:
                school_name = pdf.pdf_school
            current_app.logger.info(">>>>>>>>>>>>>>>>>>school_name:" + str(school_name))
            organization = j_organization.query.filter(j_organization.name == school_name,
                                                       j_organization.role_type == "SCHOOL").first()
            org_id = organization.id
            # 组织list，用于判断学生的组织id是否在其中，从而判断学生对应信息
            children_id_list = self._get_all_org_behind_id(org_id)
            current_app.logger.info(">>>>>>>>>>>>>>>>>children_id:" + str(children_id_list))

            upload_id = pdf.upload_id
            pdf_url = pdf.pdf_url
            pdf_uuid = str(uuid.uuid1())
            # 创建pdf存储路径
            if platform.system() == "Windows":
                pdf_path = "D:\\jinrui_pdf\\" + pdf_uuid + "\\"
            else:
                pdf_path = "/tmp/jinrui_pdf/" + pdf_uuid + "/"
            if not os.path.exists(pdf_path):
                os.makedirs(pdf_path)

            auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
            bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)

            pdf_name = pdf_url.split("/")
            pdf_oss_name = pdf_url.replace("https://{0}.{1}/".format(ALIOSS_BUCKET_NAME, ALIOSS_ENDPOINT), "")
            pdf_save_path = pdf_path + pdf_name[-1]
            # 存储pdf到本地
            result = bucket.get_object_to_file(pdf_oss_name, pdf_save_path)

            if result.status != 200:
                with db.auto_commit():
                    pdf_use = j_answer_pdf.query.filter(j_answer_pdf.pdf_id == pdf.pdf_id).first()
                    pdf_instance = pdf_use.update({
                        "pdf_status": "300303"
                    })
                    db.session.add(pdf_instance)
            else:
                with db.auto_commit():
                    pdf_use = j_answer_pdf.query.filter(j_answer_pdf.pdf_id == pdf.pdf_id).first()
                    pdf_instance = pdf_use.update({
                        "pdf_status": "300304"
                    })
                    db.session.add(pdf_instance)
                jpg_dir = self._conver_img(pdf_path, pdf_save_path, pdf_name[-1])
                current_app.logger.info(jpg_dir)

                if len(jpg_dir) % 4 != 0:
                    with db.auto_commit():
                        pdf_use = j_answer_pdf.query.filter(j_answer_pdf.pdf_id == pdf.pdf_id).first()
                        pdf_instance = pdf_use.update({
                            "pdf_status": "300303"
                        })
                        db.session.add(pdf_instance)
                else:
                    jpg_index = 0
                    # 一组卷
                    while jpg_index < len(jpg_dir):
                        booklet_id = str(uuid.uuid1())
                        jpg_dict = jpg_dir[jpg_index: jpg_index + 4]
                        jpg_path = pdf_path + jpg_dict[0]
                        # 第一页oss
                        jpg_upload_oss = self._upload_oss(jpg_dict[0], jpg_path)
                        if jpg_upload_oss["code"] == 200:
                            jpg_url = jpg_upload_oss["jpg_url"]
                        else:
                            jpg_url = None
                        # 第二页oss
                        jpg_upload_oss = self._upload_oss(jpg_dict[1], jpg_path)
                        if jpg_upload_oss["code"] == 200:
                            jpg_url_two = jpg_upload_oss["jpg_url"]
                        else:
                            jpg_url_two = None
                        # 第三页oss
                        jpg_upload_oss = self._upload_oss(jpg_dict[2], jpg_path)
                        if jpg_upload_oss["code"] == 200:
                            jpg_url_three = jpg_upload_oss["jpg_url"]
                        else:
                            jpg_url_three = None
                        # 第四页oss
                        jpg_upload_oss = self._upload_oss(jpg_dict[3], jpg_path)
                        if jpg_upload_oss["code"] == 200:
                            jpg_url_four = jpg_upload_oss["jpg_url"]
                        else:
                            jpg_url_four = None
                        jpg_oss_list = [jpg_url, jpg_url_two, jpg_url_three, jpg_url_four]
                        # 获取sn
                        current_app.logger.info(pdf_path)
                        current_app.logger.info(jpg_dict[0])
                        sn_result = self._cut_sn(pdf_path, jpg_dict[0])
                        sn = sn_result["png_result"]
                        current_app.logger.info(">>>>>>>>>>>>>>>>>>>>>sn:" + str(sn))
                        # 获取学号
                        no_result = self._cut_no(pdf_path, jpg_dict[0])
                        no = no_result["png_result"]
                        students = j_student.query.filter(j_student.student_number == no).all()
                        student_name = None
                        student_id = None
                        for student in students:
                            if student.org_id in children_id_list:
                                student_name = student.name
                                student_id = student.id
                        no_dict = {
                            "isdelete": 0,
                            "createtime": datetime.now(),
                            "updatetime": datetime.now(),
                            "png_id": str(uuid.uuid1()),
                            "png_url": no_result["png_url"],
                            "pdf_id": pdf.pdf_id,
                            "png_result": no,
                            "png_status": no_result["png_status"],
                            "png_type": no_result["png_type"],
                            "booklet_id": booklet_id,
                            "page_url": jpg_url,
                            "student_no": no,
                            "student_name": student_name,
                            "school": school_name
                        }
                        current_app.logger.info(">>>>>>>>>>>>>>>>>>>>>no:" + str(no))
                        with db.auto_commit():
                            png_instance = j_answer_png.create(no_dict)
                            db.session.add(png_instance)

                        sn_dict = {
                            "isdelete": 0,
                            "createtime": datetime.now(),
                            "updatetime": datetime.now(),
                            "png_id": str(uuid.uuid1()),
                            "png_url": sn_result["png_url"],
                            "pdf_id": pdf.pdf_id,
                            "png_result": sn,
                            "png_status": sn_result["png_status"],
                            "png_type": sn_result["png_type"],
                            "booklet_id": booklet_id,
                            "page_url": jpg_url,
                            "student_no": no,
                            "student_name": student_name,
                            "school": school_name
                        }
                        with db.auto_commit():
                            png_instance = j_answer_png.create(sn_dict)
                            db.session.add(png_instance)

                        if pdf.pdf_address == "zip":
                            zip_id = pdf.zip_id
                            zip_file = j_answer_zip.query.filter(j_answer_zip.zip_id == zip_id).first()
                            upload_by = zip_file.zip_upload_user
                        else:
                            upload_by = pdf.pdf_school

                        paper = j_paper.query.filter(j_paper.id == sn).first()
                        if paper:
                            paper_id = sn
                        else:
                            paper_id = None
                        # 封装某个学生的某套答卷dict
                        if pdf.pdf_use == "300201":
                            booklet_status = "-1"
                        else:
                            booklet_status = "1"
                        booklet_dict = {
                            "id": booklet_id,
                            "paper_id": paper_id,
                            "student_id": student_id,
                            "status": booklet_status,
                            "url": pdf.pdf_url,
                            "upload_by": upload_by,
                            "upload_id": upload_id,
                            "create_time": datetime.now().date()
                        }
                        if student_id and paper_id:
                            for sheet in json.loads(pdf.sheet_dict):
                                # jpg路径
                                # jpg_path = pdf_path + jpg_dict[sheet["page"] - 1]
                                point = "．"
                                if sheet["type"] == "select":
                                    select_list = self._cut_select(pdf_path, jpg_dict[sheet["page"] - 1], sheet)
                                    with db.auto_commit():
                                        for select in select_list:
                                            question_number = select["question_number"]
                                            question = j_question.query.filter(j_question.paper_id == paper_id,
                                                                               j_question.question_number == str(question_number))\
                                                .first()
                                            start_re = "<div>{0}{1}".format(question_number, point)
                                            if "【解析】" in question.answer:
                                                end_re = "【解析】"
                                                use_str_e = re.findall(r"{0}".format("{0}.*?{1}".format(start_re, end_re)), question.answer)[0]
                                                use_str = use_str_e.replace(start_re, "").replace(end_re, "").replace(" ", "")
                                            else:
                                                use_str = question.answer.replace(start_re, "").replace(" ", "")
                                            if use_str == str(select.get("png_result")):
                                                score = sheet["score"]
                                            else:
                                                score = 0
                                            if select.get("png_status") == "303":
                                                png_status = "303"
                                                score = None
                                            else:
                                                png_status = "304"
                                            score_id = str(uuid.uuid1())
                                            score_dict = {
                                                "id": score_id,
                                                "student_id": student_id,
                                                "booklet_id": booklet_id,
                                                "question_id": question.id,
                                                "grade_by": "system-ocr",
                                                "question_number": question_number,
                                                "score": score,
                                                "question_url": select.get("png_url"),
                                                "status": png_status
                                            }
                                            select_dict = {
                                                "isdelete": 0,
                                                "createtime": datetime.now(),
                                                "updatetime": datetime.now(),
                                                "png_id": str(uuid.uuid1()),
                                                "png_url": select.get("png_url"),
                                                "pdf_id": pdf.pdf_id,
                                                "png_result": select.get("png_result"),
                                                "png_status": select.get("png_status"),
                                                "png_type": select.get("png_type"),
                                                "booklet_id": booklet_id,
                                                "page_url": jpg_oss_list[sheet["page"] - 1],
                                                "student_no": no,
                                                "student_name": student_name,
                                                "school": school_name,
                                                "result_score": score,
                                                "result_update": score,
                                                "score_id": score_id,
                                                "question": question.content
                                            }
                                            select_instance = j_answer_png.create(select_dict)
                                            db.session.add(select_instance)
                                            score_instance = j_score.create(score_dict)
                                            db.session.add(score_instance)
                                elif sheet["type"] == "multi":
                                    multi_list = self._cut_multi(pdf_path, jpg_dict[sheet["page"] - 1], sheet)
                                    with db.auto_commit():
                                        for select in multi_list:
                                            question_number = select["question_number"]
                                            question = j_question.query.filter(j_question.paper_id == paper_id,
                                                                               j_question.question_number == str(
                                                                                   question_number)) \
                                                .first()
                                            start_re = "<div>{0}{1}".format(question_number, point)
                                            if "【解析】" in question.answer:
                                                end_re = "【解析】"
                                                use_str_e = \
                                                re.findall(r"{0}".format("{0}.*?{1}".format(start_re, end_re)),
                                                           question.answer)[0]
                                                use_str = use_str_e.replace(start_re, "").replace(end_re, "").replace(
                                                    " ", "")
                                            else:
                                                use_str = question.answer.replace(start_re, "").replace(" ", "")
                                            if use_str == str(select.get("png_result")):
                                                score = sheet["score"]
                                            else:
                                                score = 0
                                            if select.get("png_status") == "303":
                                                png_status = "303"
                                                score = None
                                            else:
                                                png_status = "304"
                                            score_id = str(uuid.uuid1())
                                            score_dict = {
                                                "id": score_id,
                                                "student_id": student_id,
                                                "booklet_id": booklet_id,
                                                "question_id": question.id,
                                                "grade_by": "system-ocr",
                                                "question_number": question_number,
                                                "score": score,
                                                "question_url": select.get("png_url"),
                                                "status": png_status
                                            }
                                            select_dict = {
                                                "isdelete": 0,
                                                "createtime": datetime.now(),
                                                "updatetime": datetime.now(),
                                                "png_id": str(uuid.uuid1()),
                                                "png_url": select.get("png_url"),
                                                "pdf_id": pdf.pdf_id,
                                                "png_result": select.get("png_result"),
                                                "png_status": select.get("png_status"),
                                                "png_type": select.get("png_type"),
                                                "booklet_id": booklet_id,
                                                "page_url": jpg_oss_list[sheet["page"] - 1],
                                                "student_no": no,
                                                "student_name": student_name,
                                                "school": school_name,
                                                "result_score": score,
                                                "result_update": score,
                                                "score_id": score_id,
                                                "question": question.content
                                            }
                                            select_instance = j_answer_png.create(select_dict)
                                            db.session.add(select_instance)
                                            score_instance = j_score.create(score_dict)
                                            db.session.add(score_instance)
                                elif sheet["type"] == "judge":
                                    judge_list = self._cut_judge(pdf_path, jpg_dict[sheet["page"] - 1], sheet)
                                    with db.auto_commit():
                                        for select in judge_list:
                                            question_number = select["question_number"]
                                            question = j_question.query.filter(j_question.paper_id == paper_id,
                                                                               j_question.question_number == str(
                                                                                   question_number)) \
                                                .first()
                                            start_re = "<div>{0}{1}".format(question_number, point)
                                            if "【解析】" in question.answer:
                                                end_re = "【解析】"
                                                use_str_e = \
                                                re.findall(r"{0}".format("{0}.*?{1}".format(start_re, end_re)),
                                                           question.answer)[0]
                                                use_str = use_str_e.replace(start_re, "").replace(end_re, "").replace(
                                                    " ", "")
                                            else:
                                                use_str = question.answer.replace(start_re, "").replace(" ", "")
                                            if use_str == str(select.get("png_result")):
                                                score = sheet["score"]
                                            else:
                                                score = 0
                                            if select.get("png_status") == "303":
                                                png_status = "303"
                                                score = None
                                            else:
                                                png_status = "304"
                                            score_id = str(uuid.uuid1())
                                            score_dict = {
                                                "id": score_id,
                                                "student_id": student_id,
                                                "booklet_id": booklet_id,
                                                "question_id": question.id,
                                                "grade_by": "system-ocr",
                                                "question_number": question_number,
                                                "score": score,
                                                "question_url": select.get("png_url"),
                                                "status": png_status
                                            }
                                            select_dict = {
                                                "isdelete": 0,
                                                "createtime": datetime.now(),
                                                "updatetime": datetime.now(),
                                                "png_id": str(uuid.uuid1()),
                                                "png_url": select.get("png_url"),
                                                "pdf_id": pdf.pdf_id,
                                                "png_result": select.get("png_result"),
                                                "png_status": select.get("png_status"),
                                                "png_type": select.get("png_type"),
                                                "booklet_id": booklet_id,
                                                "page_url": jpg_oss_list[sheet["page"] - 1],
                                                "student_no": no,
                                                "student_name": student_name,
                                                "school": school_name,
                                                "result_score": score,
                                                "result_update": score,
                                                "score_id": score_id,
                                                "question": question.content
                                            }
                                            select_instance = j_answer_png.create(select_dict)
                                            db.session.add(select_instance)
                                            score_instance = j_score.create(score_dict)
                                            db.session.add(score_instance)
                                elif sheet["type"] == "fill":
                                    score_id = str(uuid.uuid1())
                                    question_number = sheet["start"]
                                    question = j_question.query.filter(j_question.paper_id == paper_id,
                                                                       j_question.question_number == str(
                                                                           question_number)) \
                                        .first()
                                    if pdf.pdf_use == "300201":
                                        fill_dict_ocr = self._cut_fill_ocr(pdf_path, jpg_dict[sheet["page"] - 1], sheet)
                                        fill_dict = self._cut_fill_all(pdf_path, jpg_dict[sheet["page"] - 1], sheet)
                                        if fill_dict_ocr.get("png_result"):
                                            png_score = int(fill_dict_ocr.get("png_result"))
                                        else:
                                            png_score = None
                                        if fill_dict_ocr.get("png_status") == "303":
                                            png_status = "303"
                                            png_score = None
                                        else:
                                            png_status = "304"
                                        if png_score > question.score:
                                            png_score = None
                                            png_status = "303"

                                        score_dict = {
                                            "id": score_id,
                                            "student_id": student_id,
                                            "booklet_id": booklet_id,
                                            "question_id": question.id,
                                            "grade_by": "system-ocr",
                                            "question_number": question_number,
                                            "score": png_score,
                                            "question_url": fill_dict.get("png_url"),
                                            "status": png_status
                                        }
                                        select_dict = {
                                            "isdelete": 0,
                                            "createtime": datetime.now(),
                                            "updatetime": datetime.now(),
                                            "png_id": str(uuid.uuid1()),
                                            "png_url": fill_dict_ocr.get("png_url"),
                                            "pdf_id": pdf.pdf_id,
                                            "png_result": fill_dict_ocr.get("png_result"),
                                            "png_status": png_status,
                                            "png_type": fill_dict_ocr.get("png_type"),
                                            "booklet_id": booklet_id,
                                            "page_url": jpg_oss_list[sheet["page"] - 1],
                                            "student_no": no,
                                            "student_name": student_name,
                                            "school": school_name,
                                            "result_score": png_score,
                                            "result_update": png_score,
                                            "score_id": score_id,
                                            "question": question.content
                                        }
                                    else:
                                        fill_dict = self._cut_fill_all(pdf_path, jpg_dict[sheet["page"] - 1], sheet)
                                        score_dict = {
                                            "id": score_id,
                                            "student_id": student_id,
                                            "booklet_id": booklet_id,
                                            "question_id": question.id,
                                            "grade_by": "system-ocr",
                                            "question_number": question_number,
                                            "score": None,
                                            "question_url": fill_dict.get("png_url"),
                                            "status": "302"
                                        }
                                        select_dict = None
                                    with db.auto_commit():
                                        if select_dict:
                                            select_instance = j_answer_png.create(select_dict)
                                            db.session.add(select_instance)
                                        score_instance = j_score.create(score_dict)
                                        db.session.add(score_instance)
                                elif sheet["type"] == "answer":
                                    score_id = str(uuid.uuid1())
                                    question_number = sheet["start"]
                                    question = j_question.query.filter(j_question.paper_id == paper_id,
                                                                       j_question.question_number == str(
                                                                           question_number)) \
                                        .first()

                                    answer_dict_ocr = self._cut_answer_ocr(pdf_path, jpg_dict[sheet["page"] - 1], sheet)
                                    answer_dict = self._cut_answer_all(pdf_path, jpg_dict[sheet["page"] - 1], sheet)
                                    if answer_dict_ocr.get("png_result"):
                                        png_score = int(answer_dict_ocr.get("png_result"))
                                    else:
                                        png_score = 0
                                    if answer_dict_ocr.get("png_status") == "303":
                                        png_status = "303"
                                        png_score = None
                                    else:
                                        png_status = "304"
                                    if pdf.pdf_use == "300201":
                                        if png_score > question.score:
                                            png_score = None
                                            png_status = "303"
                                        score_dict = {
                                            "id": score_id,
                                            "student_id": student_id,
                                            "booklet_id": booklet_id,
                                            "question_id": question.id,
                                            "grade_by": "system-ocr",
                                            "question_number": question_number,
                                            "score": png_score,
                                            "question_url": answer_dict.get("png_url"),
                                            "status": png_status
                                        }
                                        select_dict = {
                                            "isdelete": 0,
                                            "createtime": datetime.now(),
                                            "updatetime": datetime.now(),
                                            "png_id": str(uuid.uuid1()),
                                            "png_url": answer_dict_ocr.get("png_url"),
                                            "pdf_id": pdf.pdf_id,
                                            "png_result": answer_dict_ocr.get("png_result"),
                                            "png_status": png_status,
                                            "png_type": answer_dict_ocr.get("png_type"),
                                            "booklet_id": booklet_id,
                                            "page_url": jpg_oss_list[sheet["page"] - 1],
                                            "student_no": no,
                                            "student_name": student_name,
                                            "school": school_name,
                                            "result_score": png_score,
                                            "result_update": png_score,
                                            "score_id": score_id,
                                            "question": question.content
                                        }
                                    else:
                                        score_dict = {
                                            "id": score_id,
                                            "student_id": student_id,
                                            "booklet_id": booklet_id,
                                            "question_id": question.id,
                                            "grade_by": "system-ocr",
                                            "question_number": question_number,
                                            "score": None,
                                            "question_url": answer_dict.get("png_url"),
                                            "status": "302"
                                        }
                                        select_dict = None
                                    with db.auto_commit():
                                        if select_dict:
                                            select_instance = j_answer_png.create(select_dict)
                                            db.session.add(select_instance)
                                        score_instance = j_score.create(score_dict)
                                        db.session.add(score_instance)

                            with db.auto_commit():
                                if pdf.pdf_use == "300201":
                                    answer_png_with_status = j_score.query.filter(j_score.booklet_id == booklet_id, j_score.status == "303").all()
                                    if answer_png_with_status:
                                        booklet_dict["status"] = "3"
                                    else:
                                        scores = j_score.query.filter(j_score.booklet_id == booklet_id).all()
                                        score_end = 0
                                        for score in scores:
                                            score_end = score_end + int(score.score)
                                        booklet_dict["status"] = "4"
                                        booklet_dict["score"] = score_end
                                        booklet_dict["grade_time"] = datetime.now().date()
                                booklet_instance = j_answer_booklet.create(booklet_dict)
                                db.session.add(booklet_instance)
                                pdf_instance = pdf.update({
                                    "pdf_status": "300302"
                                }, null="not")
                                db.session.add(pdf_instance)
                                pdf_error_status = j_answer_pdf.query.filter(j_answer_pdf.upload_id == upload_id, j_answer_pdf.pdf_status.in_(["300301", "300303", "300304"])).all()
                                if not pdf_error_status:
                                    if pdf.pdf_use == "300201":
                                        upload_status = "无需分配"
                                    else:
                                        upload_status = "1"
                                else:
                                    upload_status = "解析失败"
                                upload = j_answer_upload.query.filter(j_answer_upload.id == upload_id).first()
                                upload_instance = upload.update({
                                    "status": upload_status
                                })
                                db.session.add(upload_instance)
                        jpg_index = jpg_index + 4

                shutil.rmtree(pdf_path)

        else:
            current_app.logger.info(">>>>>>>>>>>>>>>>>>>>>>get_pdf_num:0")

    def _conver_img(self, pdf_path, pdf_save_path, pdf_name):
        """
        将pdf转化为png
        """
        doc = fitz.Document(pdf_save_path)
        pdf_name_without_ext = pdf_name.split(".")[0]
        i = 1
        jpg_dir = []
        for pg in range(doc.pageCount):
            page = doc[pg]
            rotate = int(0)
            # 每个尺寸的缩放系数为2，这将为我们生成分辨率提高四倍的图像。
            zoom_x = 2.0
            zoom_y = 2.0
            trans = fitz.Matrix(zoom_x, zoom_y).preRotate(rotate)
            png_uuid = "png" + str(uuid.uuid1())
            pm = page.getPixmap(matrix=trans, alpha=False)
            if platform.system() == "Windows":
                pm.writePNG(pdf_path + '{0}-{1}.png'.format(png_uuid, "%04d" % i))
                jpg_dir.append('{0}-{1}.png'.format(png_uuid, "%04d" % i))
            else:
                pm.writePNG(pdf_path + '{0}-{1}.png'.format(png_uuid, "%04d" % i))
                jpg_dir.append('{0}-{1}.png'.format(png_uuid, "%04d" % i))
            i = i + 1

        return jpg_dir

    def _label2picture(self, path, cropImg, framenum, tracker):
        """
        存储图片
        path: 图片存储前缀
        cropImg: 图片
        framenum: 文件名
        tracker: 存储文件夹
        """
        if platform.system() == "Windows":
            png_path = path + tracker + '\\' + framenum + '.jpg'
        else:
            png_path = path + tracker + '/' + framenum + '.jpg'
        if (os.path.exists(path + tracker)):
            cv2.imwrite(png_path, cropImg, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
        else:
            os.makedirs(path + tracker)
            cv2.imwrite(png_path, cropImg, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

        return framenum + ".jpg", png_path

    def _upload_oss(self, file_name, file_path):
        auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
        file_fullname = file_name.split(".")[0]
        ext = file_name.split(".")[1]
        jpg_uuid = str(uuid.uuid1())

        jpg_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + file_fullname + "-" + jpg_uuid + "." + ext
        result = bucket.put_object_from_file(file_fullname + "-" + jpg_uuid + "." + ext, file_path)
        current_app.logger.info(str(result))
        return {
            "code": result.status,
            "jpg_url": jpg_url
        }

    def _cut_sn(self, path, jpg):
        """
        剪切sn号
        """
        jpg_name_without_ext = jpg.split(".")[0]
        img = cv2.imread(r"{0}".format(path + jpg))
        sn_w = 600 + self.width_less
        sn_y = 35 + self.height_less
        sn_height = 20
        sn_width = 135
        crop_img = img[int(sn_y * self.index_h): int((sn_y + sn_height) * self.index_h),
                   int(sn_w * self.index_w): int((sn_w + sn_width) * self.index_w)]

        png_name, png_path = self._label2picture(path, crop_img, "sn", jpg_name_without_ext)

        upload_oss = self._upload_oss(png_name, png_path)
        if upload_oss["code"] == 200:
            jpg_url = upload_oss["jpg_url"]
            response = requests.get("https://jinrui.sanbinit.cn/api/ocr/mock_ocr_response?image_url={0}&image_type={1}".format(jpg_url, "5"))
            current_app.logger.info(response.content)
            content = json.loads(response.content)
            if content["data"]["err"] not in ["848", "849"]:
                value = content["data"]["values"]
                png_status = "301"
            else:
                value = None
                png_status = "303"
            return {
                "png_result": value,
                "png_url": upload_oss["jpg_url"],
                "png_status": png_status,
                "png_type": "28"
            }
        else:
            return {
                "png_result": None,
                "png_url": None,
                "png_status": None,
                "png_type": None
            }

    def _cut_no(self, path, jpg):
        """
        剪切准考证号
        """
        jpg_name_without_ext = jpg.split(".")[0]
        img = cv2.imread(r"{0}".format(path + jpg))
        sn_w = 530 + self.width_less
        sn_y = 154 + self.height_less
        sn_height = 200
        sn_width = 260
        crop_img = img[int(sn_y * self.index_h): int((sn_y + sn_height) * self.index_h),
                   int(sn_w * self.index_w): int((sn_w + sn_width) * self.index_w)]
        png_name, png_path = self._label2picture(path, crop_img, "no", jpg_name_without_ext)
        upload_oss = self._upload_oss(png_name, png_path)
        if upload_oss["code"] == 200:
            jpg_url = upload_oss["jpg_url"]
            response = requests.get(
                "https://jinrui.sanbinit.cn/api/ocr/mock_ocr_response?image_url={0}&image_type={1}".format(jpg_url,
                                                                                                           "2"))
            current_app.logger.info(response.content)
            content = json.loads(response.content)
            if content["data"]["err"] not in ["848", "849"]:
                value = content["data"]["values"]
                png_status = "301"
            else:
                value = None
                png_status = "303"
            return {
                "png_result": value,
                "png_url": upload_oss["jpg_url"],
                "png_status": png_status,
                "png_type": "29"
            }
        else:
            return {
                "png_result": None,
                "png_url": None,
                "png_status": None,
                "png_type": None
            }

    def _cut_select(self, path, jpg, sheet):
        """
        剪切单选
        """
        jpg_name_without_ext = jpg.split(".")[0]
        select_x = sheet["dot"][0]
        select_y = sheet["dot"][1]
        current_app.logger.info(path + jpg)
        img = cv2.imread(path + jpg)
        j = 0
        select_list = []
        while j < sheet["num"]:
            up = 26.37 + (j % 5) * sheet["every_height"] + self.height_less
            left = (int(j / 5)) * sheet["every_width"] + self.width_less

            crop_img = img[int((select_y + up) * self.index_h): int(
                (select_y + sheet["every_height"] + up) * self.index_h),
                       int((select_x + left) * self.index_w): int(
                           (select_x + left + sheet["every_width"]) * self.index_w)]

            png_name, png_path = self._label2picture(path, crop_img, "{0}-{1}".format(sheet["type"], str(j + 1)),
                                                     jpg_name_without_ext)
            upload_oss = self._upload_oss(png_name, png_path)
            if upload_oss["code"] == 200:
                jpg_url = upload_oss["jpg_url"]
                response = requests.get(
                    "https://jinrui.sanbinit.cn/api/ocr/mock_ocr_response?image_url={0}&image_type={1}".format(jpg_url,
                                                                                                               "0"))
                current_app.logger.info(response.content)
                content = json.loads(response.content)
                if content["data"]["err"] not in ["848", "849"]:
                    value = content["data"]["values"]
                    png_status = "301"
                else:
                    value = None
                    png_status = "303"
                select_dict = {
                    "question_number": j + 1,
                    "png_result": value,
                    "png_url": upload_oss["jpg_url"],
                    "png_status": png_status,
                    "png_type": "21"
                }
            else:
                select_dict = {
                    "question_number": j + 1,
                    "png_result": None,
                    "png_url": None,
                    "png_status": None,
                    "png_type": None
                }
            select_list.append(select_dict)
            j = j + 1
        return select_list

    # 剪裁多选
    def _cut_multi(self, path, jpg, sheet):
        """
        剪裁多选
        """
        jpg_name_without_ext = jpg.split(".")[0]
        select_x = sheet["dot"][0]
        select_y = sheet["dot"][1]
        img = cv2.imread(path + jpg)
        j = 0
        select_list = []
        while j < sheet["num"]:
            up = 26.37 + (j % 5) * sheet["every_height"] + self.height_less
            left = (int(j / 5)) * sheet["every_width"] + self.width_less
            crop_img = img[int((select_y + up) * self.index_h): int(
                (select_y + sheet["every_height"] + up) * self.index_h),
                       int((select_x + left) * self.index_w): int(
                           (select_x + left + sheet["every_width"]) * self.index_w)]
            png_name, png_path = self._label2picture(path, crop_img, "{0}-{1}".format(sheet["type"], str(j + 1)),
                                                     jpg_name_without_ext)
            upload_oss = self._upload_oss(png_name, png_path)
            if upload_oss["code"] == 200:
                jpg_url = upload_oss["jpg_url"]
                response = requests.get(
                    "https://jinrui.sanbinit.cn/api/ocr/mock_ocr_response?image_url={0}&image_type={1}".format(jpg_url,
                                                                                                               "1"))
                current_app.logger.info(response.content)
                content = json.loads(response.content)
                if content["data"]["err"] not in ["848", "849"]:
                    value = content["data"]["values"]
                    png_status = "301"
                else:
                    value = None
                    png_status = "303"
                select_dict = {
                    "question_number": j + 1,
                    "png_result": value,
                    "png_url": upload_oss["jpg_url"],
                    "png_status": png_status,
                    "png_type": "22"
                }
            else:
                select_dict = {
                    "question_number": j + 1,
                    "png_result": None,
                    "png_url": None,
                    "png_status": None,
                    "png_type": None
                }
            select_list.append(select_dict)
            j = j + 1
        return select_list

    def _cut_judge(self, path, jpg, sheet):
        """
        剪裁判断
        """
        jpg_name_without_ext = jpg.split(".")[0]
        select_x = sheet["dot"][0]
        select_y = sheet["dot"][1]
        img = cv2.imread(path + jpg)
        j = 0
        select_list = []
        while j < sheet["num"]:
            up = 26.37 + (j % 5) * sheet["every_height"] + self.height_less
            left = (int(j / 5)) * sheet["every_width"] + self.width_less
            crop_img = img[int((select_y + up) * self.index_h): int(
                (select_y + sheet["every_height"] + up) * self.index_h),
                       int((select_x + left) * self.index_w): int(
                           (select_x + left + sheet["every_width"]) * self.index_w)]
            png_name, png_path = self._label2picture(path, crop_img, "{0}-{1}".format(sheet["type"], str(j + 1)),
                                                     jpg_name_without_ext)
            upload_oss = self._upload_oss(png_name, png_path)
            if upload_oss["code"] == 200:
                jpg_url = upload_oss["jpg_url"]
                response = requests.get(
                    "https://jinrui.sanbinit.cn/api/ocr/mock_ocr_response?image_url={0}&image_type={1}".format(jpg_url,
                                                                                                               "3"))
                current_app.logger.info(response.content)
                content = json.loads(response.content)
                if content["data"]["err"] not in ["848", "849"]:
                    value = content["data"]["values"]
                    png_status = "301"
                else:
                    value = None
                    png_status = "303"
                select_dict = {
                    "question_number": j + 1,
                    "png_result": value,
                    "png_url": upload_oss["jpg_url"],
                    "png_status": png_status,
                    "png_type": "23"
                }
            else:
                select_dict = {
                    "question_number": j + 1,
                    "png_result": None,
                    "png_url": None,
                    "png_status": None,
                    "png_type": None
                }
            select_list.append(select_dict)
            j = j + 1
        return select_list

    def _cut_fill_all(self, path, jpg, sheet):
        """
        全量剪裁填空
        """
        jpg_name_without_ext = jpg.split(".")[0]
        select_x = sheet["dot"][0] + self.width_less
        select_y = sheet["dot"][1] + self.height_less
        img = cv2.imread(path + jpg)
        crop_img = img[int(select_y * self.index_h): int(
            (select_y + sheet["height"]) * self.index_h),
                   int(select_x * self.index_w): int(
                       (select_x + sheet["width"]) * self.index_w)]
        png_name, png_path = self._label2picture(path, crop_img, "{0}-{1}".format(sheet["type"], sheet["start"]),
                                                 jpg_name_without_ext)
        upload_oss = self._upload_oss(png_name, png_path)
        if upload_oss["code"] == 200:
            return {
                "png_result": None,
                "png_url": upload_oss["jpg_url"],
                "png_status": None,
                "png_type": "24"
            }
        else:
            return {
                "png_result": None,
                "png_url": None,
                "png_status": None,
                "png_type": None
            }

    def _cut_fill_ocr(self, path, jpg, sheet):
        """
        剪裁填空题ocr识别区域
        """
        jpg_name_without_ext = jpg.split(".")[0]
        select_x = sheet["score_dot"][0] + self.width_less
        select_y = sheet["score_dot"][1] + self.height_less
        img = cv2.imread(path + jpg)
        crop_img = img[int(select_y * self.index_h): int(
            (select_y + sheet["score_height"]) * self.index_h),
                   int(select_x * self.index_w): int(
                       (select_x + sheet["score_width"]) * self.index_w)]
        png_name, png_path = self._label2picture(path, crop_img, "{0}-{1}".format(sheet["type"] + "-ocr", sheet["start"]),
                                                 jpg_name_without_ext)
        upload_oss = self._upload_oss(png_name, png_path)
        if upload_oss["code"] == 200:
            jpg_url = upload_oss["jpg_url"]
            response = requests.get(
                "https://jinrui.sanbinit.cn/api/ocr/mock_ocr_response?image_url={0}&image_type={1}".format(jpg_url,
                                                                                                           "4"))
            current_app.logger.info(response.content)
            content = json.loads(response.content)
            if content["data"]["err"] not in ["848", "849"]:
                value = content["data"]["values"]
                png_status = "301"
            else:
                value = None
                png_status = "303"
            return {
                "png_result": value,
                "png_url": upload_oss["jpg_url"],
                "png_status": png_status,
                "png_type": "25"
            }
        else:
            return {
                "png_result": None,
                "png_url": None,
                "png_status": None,
                "png_type": None
            }

    def _cut_answer_all(self, path, jpg, sheet):
        """
        全量剪裁简答题
        """
        jpg_name_without_ext = jpg.split(".")[0]
        select_x = sheet["dot"][0] + self.width_less
        select_y = sheet["dot"][1] + self.height_less
        img = cv2.imread(path + jpg)
        crop_img = img[int(select_y * self.index_h): int(
            (select_y + sheet["height"]) * self.index_h),
                   int(select_x * self.index_w): int(
                       (select_x + sheet["width"]) * self.index_w)]
        png_name, png_path = self._label2picture(path, crop_img, "{0}-{1}".format(sheet["type"], sheet["start"]),
                                                 jpg_name_without_ext)
        upload_oss = self._upload_oss(png_name, png_path)
        if upload_oss["code"] == 200:
            return {
                "png_result": None,
                "png_url": upload_oss["jpg_url"],
                "png_status": None,
                "png_type": "26"
            }
        else:
            return {
                "png_result": None,
                "png_url": None,
                "png_status": None,
                "png_type": None
            }

    def _cut_answer_ocr(self, path, jpg, sheet):
        """
        剪裁简答题ocr识别区域
        """
        jpg_name_without_ext = jpg.split(".")[0]
        select_x = sheet["score_dot"][0] + self.width_less
        select_y = sheet["score_dot"][1] + self.height_less
        img = cv2.imread(path + jpg)
        crop_img = img[int(select_y * self.index_h): int(
            (select_y + sheet["score_height"]) * self.index_h),
                   int(select_x * self.index_w): int(
                       (select_x + sheet["score_width"]) * self.index_w)]
        png_name, png_path = self._label2picture(path, crop_img,
                                                 "{0}-{1}".format(sheet["type"] + "-ocr", sheet["start"]),
                                                 jpg_name_without_ext)
        upload_oss = self._upload_oss(png_name, png_path)
        if upload_oss["code"] == 200:
            jpg_url = upload_oss["jpg_url"]
            response = requests.get(
                "https://jinrui.sanbinit.cn/api/ocr/mock_ocr_response?image_url={0}&image_type={1}".format(jpg_url,
                                                                                                           "4"))
            current_app.logger.info(response.content)
            content = json.loads(response.content)
            if content["data"]["err"] not in ["848", "849"]:
                value = content["data"]["values"]
                png_status = "301"
            else:
                value = None
                png_status = "303"
            return {
                "png_result": value,
                "png_url": upload_oss["jpg_url"],
                "png_status": png_status,
                "png_type": "27"
            }
        else:
            return {
                "png_result": None,
                "png_url": None,
                "png_status": None,
                "png_type": None
            }

    def _get_all_org_behind_id(self, org_id):
        """
        根据某个学校org_id获取所有子org_id的list
        """
        org_list = []

        # org_list.append(org_id)
        grade_list = j_organization.query.filter(j_organization.parent_org_id == org_id).all()
        for grade in grade_list:
            org_list.append(grade.id)
        for org in org_list:
            class_list = j_organization.query.filter(j_organization.parent_org_id == org).all()
            for class_id in class_list:
                org_list.append(class_id.id)

        org_list.append(org_id)
        return org_list


    def mock_question(self):
        test_json = {'1': "<div>1．【实数的有关概念与大小比较】下列各数中最大的是()</div><div>A．2－<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image1_5882773743013888.png'></img>B．1C.<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image1_5882773743013888.png'></img>－2D．3－<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image1_5882773743013888.png'></img></div>", '2': '<div>2．【整式的运算】下列算式正确的是()</div><div>A．x<sup>5</sup>＋x<sup>5</sup>＝x<sup>10</sup>  B．(a－b)<sup>7</sup>÷(a－b)<sup>3</sup>＝a<sup>4</sup>－b<sup>4</sup></div><div>C．(－x<sup>5</sup>)<sup>5</sup>＝－x<sup>25</sup>  D．(－x)<sup>5</sup>(－x)<sup>5</sup>＝－x<sup>10</sup></div><div><a:blip r:embed="rId7" cstate="print"></div><div>图1</div>', '3': '<div>3．【相交线与平行线】如图1，直线a∥b，直线c分别交a，b于点A，C，∠BAC的平分线交直线b于点D，若∠2＝50°，则∠1的度数是()</div><div>A．50°      B．60°        C．80°      D．100°</div>', '4': "<div>4．【分式的概念】若分式<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5882775005499392.png'></img>的值为0，则x的值为()</div><div>A．0              B．2</div><div>C．－2          D．2或－2</div>", '5': '<div>5．【三视图】图2①是矗立千年而不倒的应县木塔一角，它使用了六十多种形态各异的斗栱．斗栱是中国古代匠师们为减少立柱与横梁交接处的剪力而创造的一种独特的结构，位于柱与梁之间，斗栱是由斗、升、栱、翘、昂组成，图②是其中一个组成部件的三视图，则这个部件是()</div><div><a:blip r:embed="rId9" cstate="print"></div><div>图2</div><div><a:blip r:embed="rId10" cstate="print">   <a:blip r:embed="rId11" cstate="print">     <a:blip r:embed="rId12" cstate="print">      <a:blip r:embed="rId13" cstate="print"></div><div>   A       B        C     D</div>', '6': '<div>6．【概率的计算】七巧板是我国古代劳动人民的发明之一，被誉为“东方魔板”，它是由五块等腰直角三角形、一块正方形和一块平行四边形共七块板组成的．如图3是一个用七巧板拼成的正方形，如果在此正方形中随机取一点，那么此点取自黑色部分的概率为()</div><div>A.<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image9_5882778625183744.png\'></img>         B.<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image10_5882777731796992.png\'></img>       C.<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image11_5882776809050112.png\'></img>         D.<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image12_5882775924051968.png\'></img></div><div><a:blip r:embed="rId18" cstate="print">        <a:blip r:embed="rId19" cstate="print">       <a:blip r:embed="rId20" cstate="print"></div><div>图3           图4       图5</div>', '7': "<div>7．【平面直角坐标系】如图4，在平面直角坐标系中，设点P到原点O的距离为ρ，OP与x轴正方向的夹角为α，则用[ρ，α]表示点P的极坐标，例如：点P的坐标为(1，1)，则其极坐标为[<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image16_5882779489210368.png'></img>，45°]．若点Q的极坐标为[4，120°]，则点Q的平面坐标为()</div><div>A．(－2，2<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image17_5882780340654080.png'></img>)     B．(2，－2<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image17_5882780340654080.png'></img>)  </div><div>C．(－2<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image17_5882781234040832.png'></img>，－2)     D．(－4，－4<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image17_5882781234040832.png'></img>)</div>", '8': '<div>8．【解直角三角形的应用】如图5，学校大门出口处有一自动感应栏杆，点A是栏杆转动的支点，当车辆经过时，栏杆AE会自动升起，某天早上，栏杆发生故障，在某个位置突然卡住，这时测得栏杆升起的角度∠BAE＝127°，已知AB⊥BC，支架AB高1.2米，大门BC打开的宽度为2米，以下哪辆车可以通过？(栏杆宽度，汽车反光镜忽略不计)</div><div>(参考数据：sin37°≈0.60，cos37°≈0.80，tan37°≈0.75.车辆尺寸：长×宽×高)()</div><div>A．宝马Z4(4 200 mm×1 800 mm×1 360 mm) </div><div>B．奇瑞QQ(4 000 mm×1 600 mm×1 520 mm)</div><div>C．大众朗逸(4 600 mm×1 700 mm×1 400 mm) </div><div>D．奥迪A4(4 700 mm×1 800 mm×1 400 mm)</div>', '9': '<div>9．【图形变换】 如图6，在平行四边形ABCD中，BC＝4，现将平行四边形ABCD绕点A旋转到平行四边形AEFG的位置，其中点B，C，D分别落在点E，F，G处，且点B，E，D，F在同一直线上，如果点E恰好是对角线BD的中点，那么AB的长度是()</div><div>A．4        B．3         C．2<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image16_5882782102261760.png\'></img>         D.<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image18_5882782991454208.png\'></img></div><div><a:blip r:embed="rId24" cstate="print">      <a:blip r:embed="rId25" cstate="print"></div><div>图6              图7</div>', '10': '<div>10．【函数的图象】如图7①，一个立方体铁块放置在圆柱形水槽内，现以每秒固定的流量往水槽中注水，28 s时注满水槽，水槽内水面的高度y(cm)与注水时间x(s)之间的函数图象如图②所示，则圆柱形水槽的容积(在没放铁块的情况下)是()</div><div>A．8 000 cm<sup>3</sup> B．10 000 cm<sup>3</sup>  C．2 000π cm<sup>3</sup>  D．3 000π cm<sup>3</sup></div><div></div>', '11': '<div>11．【整式的运算】如图8所示，图①是一个边长为a的正方形剪去一个边长为1的小正方形，图②是一个边长为(a－1)的正方形．记图①，图②中阴影部分的面积分别为S<sub>1</sub>，S<sub>2</sub>，则<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image21_5882783847092224.png\'></img>可化简为________．</div><div><a:blip r:embed="rId27" cstate="print">        <a:blip r:embed="rId28" cstate="print"></div><div> 图8                 图9</div><div><a:blip r:embed="rId29" cstate="print"></div><div>图10</div>', '12': '<div>12．【全等三角形的判定】如图9，在△ABC和△BAD中，BC＝AD，请你再补充一个条件，使△ABC≌△BAD.你补充的条件是________(只填一个)．</div>', '13': '<div>13．【平均数，中位数与众数】 如图10是根据媒体提供的消息绘制的“某市各大报刊发行量统计图”，那么发行量的众数是________万份．</div>', '14': "<div>14．【整式的运算】我们知道，同底数幂的乘法法则为a<sup>m</sup>·a<sup>n</sup>＝a<sup>m</sup><sup>＋</sup><sup>n</sup>(其中a≠0，m，n为正整数)，类似地我们规定关于任意正整数m，n的一种新运算：h(m＋n)＝h(m)·h(n)，请根据这种新运算填空：</div><div>(1)若h(1)＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image25_5882784736284672.png'></img>，则h(2)＝________；</div><div>(2)若h(1)＝k(k≠0)，那么h(n)·h(2 020)＝________(用含n和k的代数式表示，其中n为正整数)．</div>", '15': '<div>15．【一次函数的应用】在一条笔直的公路上有A，B两地，甲、乙两人同时出发，甲骑自行车从A地到B地，中途出现故障后停车修理，修好车后以原速继续行驶到B地；乙骑电动车从B地到A地，到达A地后立即按原路原速返回，结果两人同时到B地．如图11是甲、乙两人与A地的距离y(km)与行驶时间x(h)之间的函数图象．当甲距离B地还有5 km时，此时乙距B地还有________km.</div><div><a:blip r:embed="rId31" cstate="print">    <a:blip r:embed="rId32" cstate="print"></div><div>     图11              图12</div>', '16': '<div>16．【弧长计算】如图12，正方形ABCD的边长为1，分别以顶点A，B，C，D为圆心，1为半径画弧，四条弧交于点E，F，G，H，则图中阴影部分的外围周长为________．</div><div></div>', '17': "<div>17．【实数的运算】(6分)计算：<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image28_5882787319975936.png'></img><img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image29_5882786485309440.png'></img>－|<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image17_5882788158836736.png'></img>－2|＋(<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image17_5882788158836736.png'></img>－3)<sup>0</sup>－<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image16_5882785638060032.png'></img>cos45°.</div><div></div><div></div><div></div><div></div><div></div>", '18': "<div>18．【解不等式组】(6分)解不等式组<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image30_5882789006086144.png'></img>并把它的解集表示在数轴上．</div><div></div><div></div><div></div><div></div>", '19': '<div>19．【统计与概率】(6分)为关注学生出行安全，调查了某班学生出行方式，调查结果分为四类：A－骑自行车，B－步行，C－坐社区巴士，D－其他，并将调査结果绘制成如图13所示的两幅不完整的统计图．</div><div>请你根据统计图，解答下列问题：</div><div>(1)本次一共调査了多少名学生？</div><div>(2)C类女生有________名，D类男生有________名，并将条形统计图补充完整；</div><div>(3)若从被调查的A类和D类学生中分别随机选取一位同学进行进一步调查，请用列表法或画树状图的方法求出所选同学中恰好是一位男同学和一位女同学的概率．</div><div><a:blip r:embed="rId36" cstate="print"></div><div>图13</div><div></div><div></div><div></div><div></div><div></div>', '20': '<div>20．【网格作图】(8分)在所给的5×5方格中，每个小正方形的边长都是1.按要求画平行四边形：</div><div>(1)在图14①中，画出一个平行四边形，使其有一个内角为45°且它的四个顶点在方格的顶点上；</div><div>(2)在图②中，画出一个平行四边形(非特殊的平行四边形)，使其周长为整数且它的四个顶点在方格的顶点上；</div><div>(3)在图③中，画出一个平行四边形，使其面积为6且它的四个顶点以及对角线交点都在方格的顶点上．</div><div><a:blip r:embed="rId37" cstate="print"></div><div>图14</div><div></div><div></div>', '21': '<div>21．【圆的切线】(8分)如图15，在△ABC中，E是AC边上的一点，且AE＝AB，∠BAC＝2∠CBE，以AB为直径作⊙O交AC于点D，交BE于点F.</div><div><a:blip r:embed="rId38" cstate="print"></div><div>图15</div><div>(1)求证：EF＝BF；</div><div>(2)求证：BC是⊙O的切线；</div><div>(3)若AB＝4，BC＝3，求DE的长．</div><div></div><div></div><div></div><div></div><div></div><div></div><div></div>', '22': '<div>22．【二次函数的综合】(10分)如图16所示，二次函数y＝ax<sup>2</sup>＋bx＋2的图象经过点A(4，0)，B(－4，－4)，且与y轴交于点C.</div><div>(1)请求出二次函数的表达式；</div><div>(2)若点M(m，n)在抛物线的对称轴上，且AM平分∠OAC，求n的值；</div><div>(3)若P是线段AB上的一个动点(不与A，B重合)，过P作PQ∥AC，与AB上方的抛物线交于点Q，与x轴交于点H，试问：是否存在这样的点Q，使PH＝2QH？若存在，请直接出点Q的坐标；若不存在，请说明理由．</div><div><a:blip r:embed="rId39" cstate="print"></div><div>图16</div><div></div><div></div><div></div><div></div><div></div>', '23': '<div>23．【阅读理解，反比例函数的综合】(10分)小韦同学十分崇拜科学家，立志成为有所发现、有所创造的人，他组建了三人探究小组，探究小组对以下问题有了发现：</div><div>如图17①，已知一次函数y＝x＋1的图象分别与x轴和y轴相交于点E，F.过一次函数y＝x＋1的图象上的动点P作PB⊥x轴，垂足是B，直线BP交反比例函数y＝－<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image35_5882789895278592.png\'></img>的图象于点Q.过点Q作QC⊥y轴，垂足是C，直线QC交一次函数y＝x＋1的图象于点A.当点P与点E重合时(如图②)，∠POA的度数是一个确定的值．</div><div>请你加入该小组，继续探究：</div><div>(1)当点P与点E重合时，∠POA＝________°；</div><div>(2)当点P不与点E重合时，(1)中的结论还成立吗？如果成立，请说明理由；如果不成立，请说明理由并求出∠POA的度数．</div><div><a:blip r:embed="rId41" cstate="print"></div><div>图17</div><div></div><div></div><div></div><div></div><div></div>', '24': '<div>24．【几何综合】(12分)综合与实践－－探究图形中角之间的等量关系及相关问题．</div><div>问题情境：</div><div>正方形ABCD中，点P是射线DB上的一个动点，过点C作CE⊥AP于点E，点Q与点P关于点E对称，连结CQ，设∠DAP＝α(0°＜α＜135°)，∠QCE＝β.</div><div>初步探究：</div><div><a:blip r:embed="rId42" cstate="print"></div><div>图18</div><div></div><div></div><div></div><div></div><div></div><div>(1)如图18①，为探究α与β的关系，勤思小组的同学画出了0°＜α＜45°时的情形，射线AP与边CD交于点F.他们得出此时α与β的关系是β＝2α.借助这一结论可得当点Q恰好落在线段BC的延长线上(如图②)时，α＝________°，β＝________°.</div><div>深入探究：</div><div>(2)敏学小组的同学画出45°＜α＜90°时的图形如图③，射线AP与边BC交于点G.请猜想此时α与β之间的等量关系，并证明结论．</div><div>拓展延伸：</div><div>(3)请你借助图④进一步探究：①当90°＜α＜135°时，α与β之间的等量关系为________；</div><div>②已知正方形边长为2，在点P运动过程中，当α＝β时，PQ的长为________．</div><div></div><div></div><div></div>'}

        for key in test_json.keys():
            with db.auto_commit():
                question_dict = j_question.query.filter(j_question.paper_id == "5552239024214016",
                                                        j_question.question_number == key).first()
                question_instance = question_dict.update({
                    "content": test_json[key]
                }, null="not")
                db.session.add(question_instance)
        return Success()

    def mock_answer(self):
        test_json = {'1': "<div>1．B【解析】 ∵正实数都大于0，负实数都小于0，正实数大于一切负实数，2.2＜<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image1_5882977204506624.png'></img>＜2.3，∴2－<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image1_5882977204506624.png'></img>＜<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image1_5882977204506624.png'></img>－2＜3－<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image1_5882977204506624.png'></img>＜1.</div>", '2': '<div>2．C【解析】 x<sup>5</sup>＋x<sup>5</sup>＝2x<sup>5</sup>，故选项A错误；</div><div>(a－b)<sup>7</sup>÷(a－b)<sup>3</sup>＝(a－b)<sup>4</sup>，故选项B错误；</div><div>(－x<sup>5</sup>)<sup>5</sup>＝－x<sup>25</sup>，故选项C正确；</div><div>(－x)<sup>5</sup>(－x)<sup>5</sup>＝x<sup>10</sup>，故选项D错误．</div>', '3': '<div>3．C【解析】 ∵a∥b，∴∠BAD＝∠2＝50°，</div><div>∵AD平分∠BAC，∴∠BAD＝∠DAC＝50°，</div><div>∴∠1＝180°－∠BAD－∠DAC＝80°.</div>', '4': "<div>4．B【解析】 由题意可知<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image2_5882978110476288.png'></img>解得x＝2.</div>", '5': '<div>5．C</div>', '6': "<div>6．C【解析】 设“东方魔板”的面积为4，则阴影部分三角形面积为1，平行四边形面积为<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5882980698361856.png'></img>，则点取自黑色部分的概率为<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image4_5882979825946624.png'></img>＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image5_5882978978697216.png'></img>.</div>", '7': "<div>7．A【解析】 ∵点Q的极坐标为[4，120°]，</div><div>∴这一点在第二象限，则在平面直角坐标系中的横坐标是－4cos60°＝－2，纵坐标是4sin60°＝2<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5882981608525824.png'></img>，</div><div>∴点Q的平面坐标为(－2，2<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5882982501912576.png'></img>)．</div>", '8': '<div>8．C【解析】 如答图，过点A作BC的平行线AG，过点N作NQ⊥BC于Q，交AG于点R，则∠BAG＝90°，</div><div><a:blip r:embed="rId13" cstate="print"></div><div>第8题答图</div><div>∵∠BAE＝127°，</div><div>∴∠EAG＝∠EAB－∠BAG＝37°.</div><div>在△NAR中，∠ARN＝90°，∠EAG＝37°，</div><div>当车宽为1.8 m，则GR＝1.8 m，故AR＝2－1.8＝0.2(m)，</div><div>∴NR＝ARtan37°≈0.2×0.75＝0.15(m)，</div><div>∴NQ＝1.2＋0.15＝1.35＜1.36，</div><div>∴宝马Z4(4 200 mm×1 800 mm×1 360 mm)无法通过，</div><div>∴奥迪A4(4 700 mm×1 800 mm×1 400 mm)无法通过，</div><div>故选项A，D不合题意；</div><div>当车宽为1.6 m，则GR＝1.6 m，故AR＝2－1.6＝0.4(m)，</div><div>∴NR＝ARtan37°≈0.4×0.75＝0.3(m)，</div><div>∴NQ＝1.2＋0.3＝1.5＜1.52，</div><div>∴奇瑞QQ(4 000 mm×1 600 mm×1 520 mm)无法通过，故此选项不合题意；</div><div>当车宽为1.7 m，则GR＝1.7 m，故AR＝2－1.7＝0.3(m)，</div><div>∴NR＝ARtan37°≈0.3×0.75＝0.225(m)，</div><div>∴NQ＝1.2＋0.225＝1.425＞1.4，</div><div>∴大众朗逸(4 600 mm×1 700 mm×1 400 mm)可以通过，故此选项符合题意．</div>', '9': "<div>9．C【解析】 ∵四边形ABCD为平行四边形，</div><div>∴AD＝BC＝4，AD∥BC，∴∠DBC＝∠ADB，</div><div>∵平行四边形ABCD绕点A旋转到平行四边形AEFG的位置，点B，E，D，F在同一直线上，</div><div>∴∠BAE＝∠DBC，AB＝AE，</div><div>∴∠BAE＝∠ADB，∠ABE＝∠AEB，</div><div>而∠AEB＝∠ADB＋∠DAE，</div><div>∴∠AEB＝∠DAB＝∠ABE，</div><div>∴DB＝DA＝4，</div><div>而点E为BD的中点，</div><div>∴BE＝2，</div><div>∵∠BAE＝∠BDA，∠ABE＝∠DBA，</div><div>∴△BAE∽△BDA，</div><div>∴AB∶BD＝BE∶BA，即AB∶4＝2∶AB，</div><div>∴AB＝2<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image8_5882983483379712.png'></img>.</div>", '10': "<div>10．A【解析】 由题意可得12 s时，水槽内水面的高度为10 cm，12 s后水槽内高度变化趋势改变，</div><div>∴正方体的棱长为10 cm，</div><div>∴正方体的体积为10<sup>3</sup>＝1 000 cm<sup>3</sup>，</div><div>设注水的速度为x cm<sup>3</sup>/s，圆柱的底面积为S cm<sup>2</sup>，</div><div>根据题意得<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image9_5882985395982336.png'></img>解得<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image10_5882984422903808.png'></img></div><div>∴圆柱形水槽的容积为400×20＝8 000 cm<sup>3</sup>.</div>", '11': "<div>11．  <img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image11_5882986260008960.png'></img>【解析】 ∵S<sub>1</sub>＝a<sup>2</sup>－1，S<sub>2</sub>＝(a－1)<sup>2</sup>，</div><div>∴<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image12_5882987128229888.png'></img>＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image13_5882987988062208.png'></img>＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image14_5882989699338240.png'></img>＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image11_5882988822728704.png'></img>.</div>", '12': '<div>12．AC＝BD(或∠CBA＝∠DAB)【解析】 欲证两三角形全等，已有条件：BC＝AD，AB＝AB，</div><div>所以补充两边夹角∠CBA＝∠DAB便可以根据SAS证明；</div><div>补充AC＝BD便可以根据SSS证明．</div><div>故补充的条件是AC＝BD(或∠CBA＝∠DAB)．</div>', '13': '<div>13．22【解析】 ∵发行量22出现了2次，出现的次数最多，</div><div>∴众数是22万份．</div>', '14': "<div>14．<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image15_5882990575947776.png'></img>k<sup>n</sup><sup>＋</sup><sup>2 020</sup></div><div>【解析】 (1)∵h(1)＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image16_5882991439974400.png'></img>，h(m＋n)＝h(m)·h(n)，</div><div>∴h(2)＝h(1＋1)＝h(1)·h(1)＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image16_5882993222553600.png'></img>×<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image16_5882993222553600.png'></img>＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image15_5882992375304192.png'></img>；</div><div>(2)∵h(1)＝k(k≠0)，h(m＋n)＝h(m)·h(n)，</div><div>∴h(n)·h(2 020)＝k<sup>n</sup>·k<sup>2 020</sup>＝k<sup>n</sup><sup>＋</sup><sup>2 020</sup>.</div>", '15': "<div>15．7.5【解析】 甲的速度为30÷[2－(1.25－0.75)]＝20 km/h，乙的速度为30 km/h，</div><div>当甲距离B地还有5 km时，甲还要行驶<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image17_5882995021910016.png'></img>＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image18_5882994115940352.png'></img>小时到达B地，此时乙距B地<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image18_5882994115940352.png'></img>×30＝7.5(km)．</div>", '16': '<div>16．<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image16_5882995902713856.png\'></img>π【解析】 如答图，连结AF，DF，</div><div><a:blip r:embed="rId25" cstate="print"></div><div>第16题答图</div><div>由圆的定义，得AD＝AF＝DF，</div><div>∴△ADF是等边三角形，</div><div>∴∠FAD＝60°，∵∠BAD＝90°，</div><div>∴∠BAF＝90°－60°＝30°，</div><div>同理，<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image20_5882996766740480.png\'></img>的圆心角是30°，</div><div>∴<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image21_5882997618184192.png\'></img>的圆心角是90°－30°×2＝30°，</div><div>∴<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image21_5883000227041280.png\'></img>＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image22_5882999392374784.png\'></img>＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image23_5882998519959552.png\'></img>，</div><div>由对称性知，图中阴影部分的外围四条弧都相等，</div><div>∴图中阴影部分的外围周长＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image24_5883001934123008.png\'></img>×4＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image16_5883001065902080.png\'></img>π.</div>', '17': "<div>17．解：原式＝4－(2－<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883004513619968.png'></img>)＋1－<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image8_5883003628621824.png'></img>×<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image25_5883002772983808.png'></img>＝4－2＋<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883004513619968.png'></img>＋1－1＝2＋<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883004513619968.png'></img>.</div>", '18': '<div>18．解：<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image26_5883006501720064.png\'></img></div><div>由①得x≤1；由②得x＞－2，</div><div>故此不等式组的解集为－2＜x≤1，</div><div>在数轴上表示如答图．</div><div><a:blip r:embed="rId33" cstate="print"></div><div>第18题答图</div>', '19': '<div>19．(2)31</div><div>解：(1)本次调查的学生数＝10÷50%＝20(名)；</div><div>(2)C类女生有20×25%－2＝3名；</div><div>D类男生有20×(1－50%－25%－15%)－1＝1名，</div><div>补全条形统计图如答图①：</div><div><a:blip r:embed="rId34" cstate="print"></div><div>第19题答图①</div><div>(3)画树状图如答图②：</div><div><a:blip r:embed="rId35" cstate="print"></div><div>第19题答图②</div><div>共有6种等可能的结果数，其中恰好是一位男同学和一位女同学的结果数为3种，</div><div>所以所选同学中恰好是一位男同学和一位女同学的概率是<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image30_5883007365746688.png\'></img>＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883008233967616.png\'></img>.</div>', '20': '<div>20．解：(1)如答图①所示；</div><div>(2)如答图②所示；</div><div>(3)如答图③所示．</div><div><a:blip r:embed="rId37"></div><div>第20题答图</div>', '21': '<div>21．解：(1)证明：∵AE＝AB，∴△ABE是等腰三角形，</div><div>∵AB为⊙O的直径，∴AF⊥BE，∴EF＝BF；</div><div>(2)证明：∵AE＝AB，</div><div>∴△ABE是等腰三角形，</div><div>∴∠ABE＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883009097994240.png\'></img>(180°－∠BAC)＝90°－<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883009097994240.png\'></img>∠BAC，</div><div>∵∠BAC＝2∠CBE，∴∠CBE＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883009987186688.png\'></img>∠BAC，</div><div>∴∠ABC＝∠ABE＋∠CBE＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image32_5883011723628544.png\'></img>＋<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883010855407616.png\'></img>∠BAC＝90°，</div><div>即AB⊥BC，∴BC是⊙O的切线；</div><div>(3)连结BD，如答图．</div><div><a:blip r:embed="rId39" cstate="print"></div><div>第21题答图</div><div>∵AB是⊙O的直径，∴∠ADB＝90°，</div><div>∵∠ABC＝90°，∴∠ADB＝∠ABC，</div><div>∵∠BAD＝∠CAB，</div><div>∴△ABD∽△ACB，∴<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image34_5883012667346944.png\'></img>＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image35_5883013535567872.png\'></img>，</div><div>∵在Rt△ABC中，AB＝4，BC＝3，</div><div>∴AC＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image36_5883014441537536.png\'></img>＝5，</div><div>∴<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image37_5883016177979392.png\'></img>＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image38_5883015326535680.png\'></img>，解得AD＝3.2，</div><div>∵AE＝AB＝4，∴DE＝AE－AD＝4－3.2＝0.8.</div><div></div><div></div>', '22': '<div>22．解：(1)将点A，B的坐标代入函数表达式，得</div><div><img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image39_5883017062977536.png\'></img>解得<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image40_5883017968947200.png\'></img></div><div>故二次函数的表达式为y＝－<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image18_5883018837168128.png\'></img>x<sup>2</sup>＋<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883019717971968.png\'></img>x＋2；</div><div>(2)如答图①，过点A作∠OAC的角平分线交y轴于点G，交二次函数对称轴于点M，</div><div>过点G作GN⊥AC于点N，二次函数对称轴交x轴于点H，</div><div>设OG＝x＝GN，则AN＝OA＝4，</div><div>OC＝2，AC＝2<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image1_5883020594581504.png\'></img>，CG＝2－x，CN＝CA－AN＝2<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image1_5883020594581504.png\'></img>－4，</div><div>则由勾股定理得(2－x)<sup>2</sup>＝x<sup>2</sup>＋(2<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image1_5883021471191040.png\'></img>－4)<sup>2</sup>，</div><div>解得x＝4<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image1_5883022356189184.png\'></img>－8，</div><div>∵MH∥OG，则<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image41_5883023203438592.png\'></img>＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image42_5883025862627328.png\'></img>，即<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image43_5883024952463360.png\'></img>＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image44_5883024084242432.png\'></img>，</div><div>则n＝MH＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image44_5883026760208384.png\'></img>x＝3<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image1_5883027641012224.png\'></img>－6；</div><div><a:blip r:embed="rId51" cstate="print">   <a:blip r:embed="rId52" cstate="print"></div><div>①        ②</div><div>第22题答图</div><div>(3)存在这样的点Q.如答图②，</div><div>将点B，A的坐标代入一次函数表达式并解得直线AB的表达式为y＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883028551176192.png\'></img>x－2①，</div><div>同理直线AC的表达式为y＝－<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883029411008512.png\'></img>x＋2，</div><div>∵PQ∥AC，则设直线PQ的表达式为y＝－<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883030296006656.png\'></img>x＋c(c＜2)②，</div><div>联立①②，解得x＝2＋c，y＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883031956951040.png\'></img>c－1，故点P<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image47_5883031134867456.png\'></img>，</div><div>联立直线PQ与抛物线的表达式并解得x＝2－2<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image48_5883032854532096.png\'></img>(舍去正值)，</div><div>故点Q(2－2<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image48_5883033680809984.png\'></img>，－1＋c＋<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image48_5883033680809984.png\'></img>)，</div><div>∵PH＝2QH，∴P，Q的纵坐标之比也为2，</div><div>即<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883034595168256.png\'></img>c－1＝±2(－1＋c＋<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image48_5883035429834752.png\'></img>)，</div><div>解得c＝－<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image49_5883036306444288.png\'></img>或－<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image50_5883037187248128.png\'></img>，</div><div>故点Q<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image51_5883038923689984.png\'></img>或<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image52_5883038084829184.png\'></img>.</div>', '23': "<div>23．(1)45</div><div>解：(1)y＝x＋1，令x＝0，则y＝1，令y＝0，则x＝－1，</div><div>即点P(－1，0)，F(0，1)，</div><div>当x＝－1时，y＝－<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image53_5883041612238848.png'></img>＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883040731435008.png'></img>，即点Q<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image54_5883039812882432.png'></img>，</div><div>点A在一次函数上y＝x＋1上，</div><div>当y＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883043323514880.png'></img>时，x＝－<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883043323514880.png'></img>，即点A<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image55_5883042451099648.png'></img>，</div><div>则AC＝OC＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883044179152896.png'></img>，故∠AOC＝45°，∴∠POA＝45°；</div><div>(2)①当点P在射线FE上(不包括端点F)时，</div><div>由直线y＝x＋1得∠PFO＝45°，</div><div>设P(a，a＋1)，则Q<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image56_5883045047373824.png'></img>，</div><div>PQ＝－<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image57_5883045911400448.png'></img>－a－1，AF＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image8_5883046771232768.png'></img><img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image58_5883047639453696.png'></img>，</div><div>∴PA＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image8_5883049375895552.png'></img><img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image59_5883048478314496.png'></img>，PF＝PA＋AF＝－<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image8_5883049375895552.png'></img>a，</div><div>∴PA·PF＝2a<sup>2</sup>＋2a＋1，</div><div>∵OP<sup>2</sup>＝a<sup>2</sup>＋(a＋1)<sup>2</sup>＝2a<sup>2</sup>＋2a＋1.</div><div>∴PA·PF＝OP<sup>2</sup>，即<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image60_5883050214756352.png'></img>＝<img src='https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image61_5883051057811456.png'></img>，</div><div>又∠APO＝∠OPF，∴△PAO∽△POF，</div><div>∴∠POA＝∠PFO＝45°；</div><div>②当点P在射线端点F处时，直线PB与双曲线无交点，不构成∠POA；</div><div>③当点P在射线FE反向延长线上(不包括端点F)时，</div><div>同理可得△AEO∽△OFP，</div><div>∴∠AOE＋∠POF＝45°，∴∠POA＝135°.</div>", '24': '<div>24．(1)3060(3)①β＝2(α－90°)②6－2<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883051917643776.png\'></img></div><div>解：(2)α与β的关系是β＝2(90°－α)．</div><div>证明：连结PC，如答图①所示，</div><div><a:blip r:embed="rId68" cstate="print"></div><div>第24题答图①</div><div>∵点Q与点P关于点E对称，</div><div>∴EP＝EQ，</div><div>∵CE⊥AP，</div><div>∴CE垂直平分PQ，</div><div>∴CP＝CQ，</div><div>∴∠QCE＝∠PCE，</div><div>∵四边形ABCD是正方形，</div><div>∴AB＝BC＝CD＝DA，∠BAD＝90°，∠ABD＝∠CBD＝45°，</div><div>在△ABP和△CBP中，<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image63_5883052840390656.png\'></img></div><div>∴△ABP≌△CBP(SAS)，</div><div>∴∠BAP＝∠BCP＝∠BAD－∠DAP＝90°－α，AP＝CP，</div><div>∵∠ABG＝∠CEG＝90°，</div><div>∴∠BAP＋∠AGB＝90°，∠GCE＋∠CGE＝90°，</div><div>∵∠AGB＝∠CGE，</div><div>∴∠BAP＝∠GCE，∴∠BCP＝∠GCE＝90°－α，</div><div>∴∠QCE＝2∠GCE＝2(90°－α)，即β＝2(90°－α)．</div><div>(3)①当90°＜α＜135°时，α与β之间的等量关系为β＝2(α－90°)．</div><div>理由如下：连结PC，设CE交AB于点H，如答图②所示：</div><div><a:blip r:embed="rId70" cstate="print"></div><div>第24题答图②</div><div>∵点Q与点P关于点E对称，</div><div>∴EP＝EQ，</div><div>∵CE⊥AP，</div><div>∴CE垂直平分PQ，</div><div>∴CP＝CQ，</div><div>∴∠PCE＝∠QCE＝β，</div><div>∵四边形ABCD是正方形，</div><div>∴AB＝BC＝CD＝DA，∠BAD＝90°，∠ABD＝∠CBD＝45°，</div><div>∴∠ABP＝∠CBP，</div><div>在△ABP和△CBP中，<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image63_5883053717000192.png\'></img></div><div>∴△ABP≌△CBP(SAS)，</div><div>∴∠BAP＝∠BCP＝∠DAP－∠BAD＝α－90°，</div><div>∵∠AEH＝∠CBH＝90°，</div><div>∴∠BAP＋∠AHE＝90°，∠BCH＋∠BHC＝90°，</div><div>∵∠AHE＝∠CHB，∴∠BAP＝∠BCH，</div><div>∴∠BCP＝∠BCH＝∠BAP＝α－90°，</div><div>∴∠QCE＝∠PCE＝2∠BCP＝2(α－90°)，即β＝2(α－90°)；</div><div>②当0°＜α＜45°时，β＝2α，不合题意；</div><div>当45°＜α＜90°时，β＝2(90°－α)，</div><div>∵α＝β，∴α＝β＝60°，作PM⊥AD于M，如答图③所示：</div><div><a:blip r:embed="rId71" cstate="print"></div><div>第24题答图③</div><div>∵∠APM＝90°－α＝30°，∠PDM＝45°，</div><div>∴AM＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883054656524288.png\'></img>AP，DM＝PM＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883055663157248.png\'></img>AM，</div><div>设AM＝x，则CP＝AP＝2x，</div><div>DM＝PM＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883056560738304.png\'></img>x，</div><div>∵AD＝2，∴x＋<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883057420570624.png\'></img>x＝2，</div><div>解得x＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883058305568768.png\'></img>－1，</div><div>∴CP＝AP＝2x＝2<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883059177984000.png\'></img>－2，</div><div>∵∠PCQ＝2β＝120°，CP＝CQ，CE⊥AP，</div><div>∴∠CPE＝30°，PE＝QE，</div><div>∴CE＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3_5883060104925184.png\'></img>CP＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883060977340416.png\'></img>－1，</div><div>PE＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883061845561344.png\'></img>CE＝3－<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883061845561344.png\'></img>，</div><div>∴PQ＝2PE＝6－2<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883062726365184.png\'></img>；</div><div>当90°＜α＜135°时，β＝2(α－90°)，</div><div>∵α＝β，∴α＝β＝180°，不合题意．</div><div>综上所述，在点P运动过程中，当α＝β时，PQ的长为6－2<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6_5883063586197504.png\'></img>.</div><div>则HQ＝<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image25_5883064450224128.png\'></img>QT，PQ＋<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image25_5883064450224128.png\'></img>QT＝PQ＋QH，</div><div>当点P与点R重合，P，Q，H在一条直线且与直线HT垂直时，PQ＋<img src=\'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image25_5883065289084928.png\'></img>QT有最小值，其最小值为y<sub>T</sub>－y<sub>R</sub>＝5－1＝4.</div><div></div>'}

        for key in test_json.keys():
            with db.auto_commit():
                question_dict = j_question.query.filter(j_question.paper_id == "5552239024214016",
                                                        j_question.question_number == key).first()
                question_instance = question_dict.update({
                    "answer": test_json[key],
                    "explanation": test_json[key]
                }, null="not")
                db.session.add(question_instance)
        return Success()

    def mock_booklet(self):
        pdf = j_answer_pdf.query.filter(j_answer_pdf.isdelete == 0, j_answer_pdf.pdf_status == "300305") \
            .order_by(j_answer_pdf.createtime.desc()).first()
        if pdf and pdf.pdf_ip:
            # 判断pdf可用性，如果pdf可用，继续执行
            # 获取组织信息
            school_network = j_school_network.query.filter(j_school_network.net_ip == pdf.pdf_ip).first()
            if school_network:
                school_name = school_network.school_name
            else:
                school_name = pdf.pdf_school
            current_app.logger.info(">>>>>>>>>>>>>>>>>>school_name:" + str(school_name))
            organization = j_organization.query.filter(j_organization.name == school_name,
                                                       j_organization.role_type == "SCHOOL").first()
            org_id = organization.id
            # 组织list，用于判断学生的组织id是否在其中，从而判断学生对应信息
            children_id_list = self._get_all_org_behind_id(org_id)
            current_app.logger.info(">>>>>>>>>>>>>>>>>children_id:" + str(children_id_list))

            upload_id = pdf.upload_id

            pdf_url = pdf.pdf_url
            pdf_uuid = str(uuid.uuid1())
            # 创建pdf存储路径
            if platform.system() == "Windows":
                pdf_path = "D:\\jinrui_pdf\\" + pdf_uuid + "\\"
            else:
                pdf_path = "/tmp/jinrui_pdf/" + pdf_uuid + "/"
            if not os.path.exists(pdf_path):
                os.makedirs(pdf_path)

            auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
            bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)

            pdf_name = pdf_url.split("/")
            pdf_save_path = pdf_path + pdf_name[-1]
            # 存储pdf到本地
            result = bucket.get_object_to_file(pdf_name[-1], pdf_save_path)
            current_app.logger.info(">>>>>>>>>>>>>>>oss:" + str(result.status))

            paper_name = pdf.paper_name

            paper = j_paper.query.filter(j_paper.name == paper_name).first()

            if result.status != 200:
                with db.auto_commit():
                    pdf_use = j_answer_pdf.query.filter(j_answer_pdf.pdf_id == pdf.pdf_id).first()
                    pdf_instance = pdf_use.update({
                        "pdf_status": "300303"
                    })
                    db.session.add(pdf_instance)
                raise Exception("下载pdf失败，失败pdf_id:{0}".format(pdf.pdf_id))
            else:
                with db.auto_commit():
                    pdf_use = j_answer_pdf.query.filter(j_answer_pdf.pdf_id == pdf.pdf_id).first()
                    pdf_instance = pdf_use.update({
                        "pdf_status": "300304"
                    })
                    db.session.add(pdf_instance)

                current_app.logger.info(">>>>>>>>>>>>update_pdf_status")
                jpg_dir = self._conver_img(pdf_path, pdf_save_path, pdf_name[-1])

                current_app.logger.info(jpg_dir)
                current_app.logger.info(pdf.sheet_dict)

                page_one_dict = {}
                page_two_dict = {}
                page_three_dict = {}
                page_four_dict = {}
                for page_dict in json.loads(pdf.sheet_dict):
                    current_app.logger.info(page_dict)
                    if page_dict["page"] == 1:
                        page_one_dict = self._make_dict_ocr(page_dict, pdf)
                    elif page_dict["page"] == 2:
                        page_two_dict = self._make_dict_ocr(page_dict, pdf)
                    elif page_dict["page"] == 3:
                        page_three_dict = self._make_dict_ocr(page_dict, pdf)
                    elif page_dict["page"] == 4:
                        page_four_dict = self._make_dict_ocr(page_dict, pdf)

                jpg_index = 0
                while jpg_index < len(jpg_dir):
                    jpg_dict = jpg_dir[jpg_index: jpg_index + 4]
                    current_app.logger.info(jpg_dict)
                    response_one = self._use_ocr(pdf_path + jpg_dict[0], page_one_dict)
                    current_app.logger.info(">>>>>>>>>>>>>>>>>>>>>>>>>第一张图片算法返回：" + str(response_one))
                    # oss
                    auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                    bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                    page_one_file_fullname = (pdf_path.replace("/tmp", "tmp") + jpg_dict[0]).split(".")[0]
                    page_one_ext = (pdf_path + jpg_dict[0]).split(".")[1]
                    jpg_uuid = str(uuid.uuid1())

                    page_one_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + page_one_file_fullname + "." + page_one_ext
                    result = bucket.put_object_from_file(page_one_file_fullname + "." + page_one_ext,
                                                         pdf_path + jpg_dict[0])
                    current_app.logger.info(str(result))

                    page_two_file_fullname = (pdf_path.replace("/tmp", "tmp") + jpg_dict[1]).split(".")[0]
                    page_two_ext = (pdf_path + jpg_dict[0]).split(".")[1]

                    page_two_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + page_two_file_fullname + "." + page_two_ext
                    result = bucket.put_object_from_file(page_two_file_fullname + "." + page_two_ext,
                                                         pdf_path + jpg_dict[0])
                    current_app.logger.info(str(result))

                    page_three_file_fullname = (pdf_path.replace("/tmp", "tmp") + jpg_dict[2]).split(".")[0]
                    page_three_ext = (pdf_path + jpg_dict[0]).split(".")[1]

                    page_three_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + page_three_file_fullname + "." + page_three_ext
                    result = bucket.put_object_from_file(page_three_file_fullname + "." + page_three_ext,
                                                         pdf_path + jpg_dict[0])
                    current_app.logger.info(str(result))

                    page_four_file_fullname = (pdf_path.replace("/tmp", "tmp") + jpg_dict[3]).split(".")[0]
                    page_four_ext = (pdf_path + jpg_dict[0]).split(".")[1]

                    page_four_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + page_four_file_fullname + "." + page_four_ext
                    result = bucket.put_object_from_file(page_four_file_fullname + "." + page_four_ext,
                                                         pdf_path + jpg_dict[0])
                    current_app.logger.info(str(result))

                    sn = None
                    student_no = None
                    student_no_id = None
                    booklet_id = str(uuid.uuid1())
                    student_name = None
                    student_id = None
                    is_miss = "302"

                    if response_one and response_one["status"] == 200:
                        result = response_one["data"]
                        result_list = result["dirct"]
                        for result_dict in result_list:
                            if result_dict["index"] == "-3":
                                sn = result_dict["ocr_result"]
                                paper = j_paper.query.filter(j_paper.id == sn).first()
                                current_app.logger.info(">>>>>>>>>>>>>>sn:" + sn)
                                current_app.logger.info(">>>>>>>>>>>>>>jpg_index:" + str(jpg_index))
                                current_app.logger.info(">>>>>>>>>>>>>>page_one_url:" + page_one_url)
                                if paper and paper.name == pdf.paper_name:
                                    status = "301"
                                    pic_path = result_dict["cut_img_path"]
                                    # oss
                                    auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                                    bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                                    file_fullname = pic_path.replace("/tmp", "tmp").split(".")[0]
                                    current_app.logger.info(">>>>>>>>>>>>pic_path:" + str(pic_path))
                                    ext = pic_path.split(".")[-1]
                                    jpg_uuid = str(uuid.uuid1())

                                    jpg_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + file_fullname + "-" + jpg_uuid + "." + ext
                                    result = bucket.put_object_from_file(file_fullname + "." + ext,
                                                                         pic_path)
                                    current_app.logger.info(str(result))
                                    student_no_id = str(uuid.uuid1())
                                    with db.auto_commit():
                                        png_instance = j_answer_png.create({
                                            "isdelete": 0,
                                            "createtime": datetime.now(),
                                            "updatetime": datetime.now(),
                                            "png_id": student_no_id,
                                            "png_url": jpg_url,
                                            "pdf_id": pdf.pdf_id,
                                            "png_result": sn,
                                            "png_status": status,
                                            "png_type": "28",
                                            "question": None,
                                            "booklet_id": booklet_id,
                                            "page_url": page_one_url,
                                            "student_no": student_no,
                                            "student_no_id": student_no_id,
                                            "student_name": student_name,
                                            "school": school_name,
                                            "result_score": None,
                                            "result_update": None,
                                            "score_id": None
                                        })
                                        db.session.add(png_instance)
                                else:
                                    current_app.logger.info("该pdf存在异常答卷")
                                    with db.auto_commit():
                                        pdf_use = j_answer_pdf.query.filter(j_answer_pdf.pdf_id == pdf.pdf_id).first()
                                        pdf_instance = pdf_use.update({
                                            "pdf_status": "300303"
                                        })
                                        db.session.add(pdf_instance)
                                    raise Exception("答卷异常")
                            if result_dict["index"] == "-2":
                                # 缺考
                                if result_dict["ocr_result"] == "1":
                                    is_miss = "301"
                            if result_dict["index"] == "-4":
                                student_no = result_dict["ocr_result"]
                                student = j_student.query.filter(j_student.student_number == student_no).first()
                                if student:
                                    status = 301
                                    student_name = student.name
                                    student_id = student.id
                                else:
                                    status = 303
                                    student_name = None
                                    student_id = None
                                pic_path = result_dict["cut_img_path"]
                                # oss
                                auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                                bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                                file_fullname = pic_path.replace("/tmp", "tmp").split(".")[0]
                                ext = pic_path.split(".")[-1]
                                jpg_uuid = str(uuid.uuid1())

                                jpg_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + file_fullname + "-" + jpg_uuid + "." + ext
                                result = bucket.put_object_from_file(file_fullname + "." + ext,
                                                                     pic_path)
                                current_app.logger.info(str(result))
                                student_no_id = str(uuid.uuid1())
                                with db.auto_commit():
                                    png_instance = j_answer_png.create({
                                        "isdelete": 0,
                                        "createtime": datetime.now(),
                                        "updatetime": datetime.now(),
                                        "png_id": student_no_id,
                                        "png_url": jpg_url,
                                        "pdf_id": pdf.pdf_id,
                                        "png_result": student_no,
                                        "png_status": status,
                                        "png_type": "29",
                                        "question": None,
                                        "booklet_id": booklet_id,
                                        "page_url": page_one_url,
                                        "student_no": student_no,
                                        "student_no_id": student_no_id,
                                        "student_name": student_name,
                                        "school": school_name,
                                        "result_score": None,
                                        "result_update": None,
                                        "score_id": None
                                    })
                                    db.session.add(png_instance)

                    else:
                        current_app.logger.info("第{0}页识别失败".format(str(jpg_index + 1)))

                    if sn and student_no:
                        if is_miss == "301":
                            question_list = j_question.query.filter(j_question.paper_id == sn).all()
                            with db.auto_commit():
                                for question in question_list:
                                    score_dict = {
                                        "id": str(uuid.uuid1()),
                                        "student_id": student_id,
                                        "booklet_id": booklet_id,
                                        "question_id": question.id,
                                        "grade_by": "system-ocr",
                                        "question_number": question.question_number,
                                        "score": 0,
                                        "question_url": None,
                                        "status": "304"
                                    }
                                    score_instance = j_score.create(score_dict)
                                    db.session.add(score_instance)
                                booklet_dict = {
                                    "id": booklet_id,
                                    "paper_id": paper.id,
                                    "student_id": student_id,
                                    "status": "4",
                                    "score": 0,
                                    "grade_time": datetime.now().date(),
                                    "create_time": datetime.now().date(),
                                    "url": pdf.pdf_url,
                                    "upload_by": pdf.pdf_school,
                                    "grade_num": None,
                                    "upload_id": pdf.upload_id,
                                    "is_miss": "301"
                                }
                                booklet_instance = j_answer_booklet.create(booklet_dict)
                                db.session.add(booklet_instance)

                        else:
                            if response_one and response_one["status"] == 200:
                                result = response_one["data"]
                                result_list = result["dirct"]
                                for result_dict in result_list:
                                    pic_path = result_dict["cut_img_path"]
                                    # oss
                                    auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                                    bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                                    file_fullname = pic_path.replace("/tmp", "tmp").split(".")[0]
                                    ext = pic_path.split(".")[-1]
                                    jpg_uuid = str(uuid.uuid1())

                                    jpg_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + file_fullname + "." + ext
                                    result = bucket.put_object_from_file(file_fullname + "." + ext,
                                                                         pic_path)
                                    current_app.logger.info(str(result))
                                    if result_dict["type"] in ["21", "22", "23"]:
                                        self._read_over_select_multi_judge(result_dict, paper, jpg_url, pdf, student_no,
                                                                           booklet_id, page_one_url, student_no_id, student_name,
                                                                           school_name, student_id)
                                    if result_dict["type"] == "25":
                                        self._read_over_fill(result_dict, paper, jpg_url, pdf, student_no,
                                                                           booklet_id, page_one_url, student_no_id, student_name,
                                                                           school_name, student_id, pdf.pdf_use)
                                    if result_dict["type"] == "27":
                                        self._read_over_answer(result_dict, paper, jpg_url, pdf, student_no,
                                                             booklet_id, page_one_url, student_no_id, student_name,
                                                             school_name, student_id, pdf.pdf_use)
                            else:
                                current_app.logger.info("第{0}页识别失败".format(str(jpg_index + 1)))

                            response_two = self._use_ocr(pdf_path + jpg_dict[1], page_two_dict)
                            if response_two and response_two["status"] == 200:
                                result = response_two["data"]
                                result_list = result["dirct"]
                                for result_dict in result_list:
                                    pic_path = result_dict["cut_img_path"]
                                    # oss
                                    auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                                    bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                                    file_fullname = pic_path.replace("/tmp", "tmp").split(".")[0]
                                    ext = pic_path.split(".")[-1]
                                    jpg_uuid = str(uuid.uuid1())

                                    jpg_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + file_fullname + "." + ext
                                    result = bucket.put_object_from_file(file_fullname + "." + ext,
                                                                         pic_path)
                                    current_app.logger.info(str(result))
                                    if result_dict["type"] in ["21", "22", "23"]:
                                        self._read_over_select_multi_judge(result_dict, paper, jpg_url, pdf, student_no,
                                                                           booklet_id, page_two_url, student_no_id, student_name,
                                                                           school_name, student_id)
                                    if result_dict["type"] == "25":
                                        self._read_over_fill(result_dict, paper, jpg_url, pdf, student_no,
                                                                           booklet_id, page_two_url, student_no_id, student_name,
                                                                           school_name, student_id, pdf.pdf_use)
                                    if result_dict["type"] == "27":
                                        self._read_over_answer(result_dict, paper, jpg_url, pdf, student_no,
                                                             booklet_id, page_two_url, student_no_id, student_name,
                                                             school_name, student_id, pdf.pdf_use)
                            else:
                                current_app.logger.info("第{0}页识别失败".format(str(jpg_index + 2)))

                            response_three = self._use_ocr(pdf_path + jpg_dict[2], page_three_dict)
                            if response_three and response_three["status"] == 200:
                                result = response_three["data"]
                                result_list = result["dirct"]
                                for result_dict in result_list:
                                    pic_path = result_dict["cut_img_path"]
                                    # oss
                                    auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                                    bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                                    file_fullname = pic_path.replace("/tmp", "tmp").split(".")[0]
                                    ext = pic_path.split(".")[-1]
                                    jpg_uuid = str(uuid.uuid1())

                                    jpg_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + file_fullname + "." + ext
                                    result = bucket.put_object_from_file(file_fullname + "." + ext,
                                                                         pic_path)
                                    current_app.logger.info(str(result))
                                    if result_dict["type"] in ["21", "22", "23"]:
                                        self._read_over_select_multi_judge(result_dict, paper, jpg_url, pdf, student_no,
                                                                           booklet_id, page_three_url, student_no_id, student_name,
                                                                           school_name, student_id)
                                    if result_dict["type"] == "25":
                                        self._read_over_fill(result_dict, paper, jpg_url, pdf, student_no,
                                                                           booklet_id, page_three_url, student_no_id, student_name,
                                                                           school_name, student_id, pdf.pdf_use)
                                    if result_dict["type"] == "27":
                                        self._read_over_answer(result_dict, paper, jpg_url, pdf, student_no,
                                                             booklet_id, page_three_url, student_no_id, student_name,
                                                             school_name, student_id, pdf.pdf_use)
                            else:
                                current_app.logger.info("第{0}页识别失败".format(str(jpg_index + 3)))

                            response_four = self._use_ocr(pdf_path + jpg_dict[3], page_four_dict)

                            if response_four and response_four["status"] == 200:
                                result = response_four["data"]
                                result_list = result["dirct"]
                                for result_dict in result_list:
                                    pic_path = result_dict["cut_img_path"]
                                    # oss
                                    auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                                    bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                                    file_fullname = pic_path.replace("/tmp", "tmp").split(".")[0]
                                    ext = pic_path.split(".")[-1]
                                    jpg_uuid = str(uuid.uuid1())

                                    jpg_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + file_fullname + "." + ext
                                    result = bucket.put_object_from_file(file_fullname + "." + ext,
                                                                         pic_path)
                                    current_app.logger.info(str(result))
                                    if result_dict["type"] in ["21", "22", "23"]:
                                        self._read_over_select_multi_judge(result_dict, paper, jpg_url, pdf, student_no,
                                                                           booklet_id, page_four_url, student_no_id, student_name,
                                                                           school_name, student_id)
                                    if result_dict["type"] == "25":
                                        self._read_over_fill(result_dict, paper, jpg_url, pdf, student_no,
                                                                           booklet_id, page_four_url, student_no_id, student_name,
                                                                           school_name, student_id, pdf.pdf_use)
                                    if result_dict["type"] == "27":
                                        self._read_over_answer(result_dict, paper, jpg_url, pdf, student_no,
                                                             booklet_id, page_four_url, student_no_id, student_name,
                                                             school_name, student_id, pdf.pdf_use)
                            else:
                                current_app.logger.info("第{0}页识别失败".format(str(jpg_index + 4)))

                            scores_error = j_score.query.filter(j_score.booklet_id == booklet_id,
                                                                j_score.status.in_(["303", "302"])).all()
                            if pdf.pdf_use == "300201":
                                if not scores_error:
                                    booklet_status = "4"
                                    scores_all = j_score.query.filter(j_score.booklet_id == booklet_id,
                                                                    j_score.status == "304").all()
                                    booklet_score = 0
                                    for scores in scores_all:
                                        booklet_score += scores.score
                                else:
                                    booklet_status = "3"
                                    booklet_score = None
                            else:
                                booklet_status = "1"
                                booklet_score = None
                            booklet_dict = {
                                "id": booklet_id,
                                "paper_id": paper.id,
                                "student_id": student_id,
                                "status": booklet_status,
                                "score": booklet_score,
                                "grade_time": datetime.now().date(),
                                "create_time": datetime.now().date(),
                                "url": json.dumps([page_one_url, page_two_url, page_three_url, page_four_url]),
                                "upload_by": pdf.pdf_school,
                                "grade_num": None,
                                "upload_id": pdf.upload_id,
                                "is_miss": "302"
                            }
                            with db.auto_commit():
                                booklet_instance = j_answer_booklet.create(booklet_dict)
                                db.session.add(booklet_instance)
                    else:
                        current_app.logger.info("该答卷识别失败,pdf_id:{0},失败页码为{1}-{2}"
                                                .format(pdf.pdf_id, str(jpg_index + 1), str(jpg_index + 4)))
                    jpg_index += 4

                with db.auto_commit():
                    pdf_use = j_answer_pdf.query.filter(j_answer_pdf.pdf_id == pdf.pdf_id).first()
                    pdf_instance = pdf_use.update({
                        "pdf_status": "300302"
                    })
                    db.session.add(pdf_instance)

                with db.auto_commit():
                    pdf_error_status = j_answer_pdf.query.filter(j_answer_pdf.upload_id == upload_id,
                                                                 j_answer_pdf.pdf_status.in_(
                                                                     ["300305", "300303", "300304"])).all()
                    if not pdf_error_status:
                        if pdf.pdf_use == "300201":
                            upload_status = "无需分配"
                        else:
                            upload_status = "1"
                    else:
                        upload_status = "解析失败"
                    upload = j_answer_upload.query.filter(j_answer_upload.id == upload_id).first()
                    current_app.logger.info(">>>>>>>>>>>>>>>>>upload_id:" + str(upload_id))
                    upload_instance = upload.update({
                        "status": upload_status
                    }, null="not")
                    db.session.add(upload_instance)

                auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                result = bucket.delete_object(pdf_name[-1])
                current_app.logger.info(">>>>>>>>>>>oss_delete:" + str(result.status))
                current_app.logger.info(">>>>>>>>>>>delete_pdf_name" + pdf_name[-1])

                shutil.rmtree(pdf_path)

        else:
            current_app.logger.info(">>>>>>>>>>>>>>>>>>>>>>get_pdf_num:0")

    def _make_dict(self, page_dict, test_item):
        page_ocr_dict = {}
        page_ocr_dict["width"] = page_dict["width"]
        page_ocr_dict["height"] = page_dict["height"]
        page_ocr_dict["uuid"] = str(uuid.uuid1())
        page_ocr_dict["ocr_dict"] = []
        for dot in page_dict["data"]:
            if dot["type"] == "sn":
                dot_dict = {}
                dot_dict["ocr_dot"] = dot["dot"]
                dot_dict["cut_dot"] = dot["dot"]
                dot_dict["ocr_height"] = dot["height"]
                dot_dict["index"] = None
                dot_dict["ocr_width"] = dot["width"]
                dot_dict["cut_height"] = dot["height"]
                dot_dict["cut_width"] = dot["width"]
                dot_dict["type"] = "28"
                dot_dict["img_use"] = "300201"
                dot_dict["result"] = None
                dot_dict["result_status"] = None
                dot_dict["img_path"] = None
                page_ocr_dict["ocr_dict"].append(dot_dict)
            elif dot["type"] == "no":
                dot_dict = {}
                dot_dict["ocr_dot"] = dot["dot"]
                dot_dict["cut_dot"] = dot["dot"]
                dot_dict["ocr_height"] = dot["height"]
                dot_dict["index"] = None
                dot_dict["ocr_width"] = dot["width"]
                dot_dict["cut_height"] = dot["height"]
                dot_dict["cut_width"] = dot["width"]
                dot_dict["type"] = "29"
                dot_dict["img_use"] = "300201"
                dot_dict["result"] = None
                dot_dict["result_status"] = None
                dot_dict["img_path"] = None
                page_ocr_dict["ocr_dict"].append(dot_dict)
            elif dot["type"] == "miss":
                dot_dict = {}
                dot_dict["ocr_dot"] = dot["dot"]
                dot_dict["cut_dot"] = dot["dot"]
                dot_dict["ocr_height"] = dot["height"]
                dot_dict["index"] = None
                dot_dict["ocr_width"] = dot["width"]
                dot_dict["cut_height"] = dot["height"]
                dot_dict["cut_width"] = dot["width"]
                dot_dict["type"] = "20"
                dot_dict["img_use"] = "300201"
                dot_dict["result"] = None
                dot_dict["result_status"] = None
                dot_dict["img_path"] = None
                page_ocr_dict["ocr_dict"].append(dot_dict)
            elif dot["type"] == "select":
                j = 0
                """
                dot_dict = {}
                dot_dict["ocr_dot"] = dot["dot"]
                dot_dict["cut_dot"] = dot["dot"]
                dot_dict["ocr_height"] = dot["height"]
                dot_dict["cut_height"] = dot["height"]
                dot_dict["index"] = "{0}".format(str(dot["start"] + j))
                dot_dict["ocr_width"] = dot["width"]
                dot_dict["cut_width"] = dot["width"]
                dot_dict["type"] = "21"
                dot_dict["img_use"] = "300201"
                dot_dict["result"] = None
                dot_dict["result_status"] = None
                dot_dict["img_path"] = None
                page_ocr_dict["ocr_dict"].append(dot_dict)
                """
                while j < dot["num"]:
                    dot_dict = {}
                    up = 28.339 + (j % 5) * dot["every_height"] + dot["dot"][1]
                    left = (int(j / 5)) * dot["every_width"] + dot["dot"][0]
                    dot_dict["ocr_dot"] = [left, up]
                    dot_dict["cut_dot"] = [left, up]
                    dot_dict["ocr_height"] = dot["every_height"]
                    dot_dict["cut_height"] = dot["every_height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"] + j))
                    dot_dict["ocr_width"] = dot["every_width"]
                    dot_dict["cut_width"] = dot["every_width"]
                    dot_dict["type"] = "21"
                    dot_dict["img_use"] = "300201"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)
                    j += 1
            elif dot["type"] == "multi":
                j = 0
                while j < dot["num"]:
                    dot_dict = {}
                    up = 28.339 + (j % 5) * dot["every_height"] + dot["dot"][1]
                    left = (int(j / 5)) * dot["every_width"] + dot["dot"][0]
                    dot_dict["ocr_dot"] = [left, up]
                    dot_dict["cut_dot"] = [left, up]
                    dot_dict["ocr_height"] = dot["every_height"]
                    dot_dict["cut_height"] = dot["every_height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"] + j))
                    dot_dict["ocr_width"] = dot["every_width"]
                    dot_dict["cut_width"] = dot["every_width"]
                    dot_dict["type"] = "22"
                    dot_dict["img_use"] = "300201"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)
                    j += 1
            elif dot["type"] == "judge":
                j = 0
                while j < dot["num"]:
                    dot_dict = {}
                    up = 28.339 + (j % 5) * dot["every_height"] + dot["dot"][1]
                    left = (int(j / 5)) * dot["every_width"] + dot["dot"][0]
                    dot_dict["ocr_dot"] = [left, up]
                    dot_dict["cut_dot"] = [left, up]
                    dot_dict["ocr_height"] = dot["every_height"]
                    dot_dict["cut_height"] = dot["every_height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"] + j))
                    dot_dict["ocr_width"] = dot["every_width"]
                    dot_dict["cut_width"] = dot["every_width"]
                    dot_dict["type"] = "23"
                    dot_dict["img_use"] = "300201"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)
                    j += 1
            elif dot["type"] == "fill":
                if dot["show_title"] == 1:
                    # dot["every_height"] += dot["title_height"]
                    dot["dot"][1] += dot["title_height"]
                if test_item.test_use == "300201":
                    dot_dict = {}
                    dot_dict["ocr_dot"] = dot["score_dot"]
                    dot_dict["cut_dot"] = dot["dot"]
                    dot_dict["ocr_height"] = dot["score_height"]
                    dot_dict["cut_height"] = dot["every_height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"]))
                    dot_dict["ocr_width"] = dot["score_width"]
                    dot_dict["cut_width"] = dot["every_width"]
                    dot_dict["type"] = "25"
                    dot_dict["img_use"] = "300201"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)
                elif test_item.test_use == "300202":
                    dot_dict = {}
                    dot_dict["ocr_dot"] = None
                    dot_dict["cut_dot"] = dot["dot"]
                    dot_dict["ocr_height"] = None
                    dot_dict["cut_height"] = dot["every_height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"]))
                    dot_dict["ocr_width"] = None
                    dot_dict["cut_width"] = dot["every_width"]
                    dot_dict["type"] = "25"
                    dot_dict["img_use"] = "300202"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)
            elif dot["type"] == "answer":
                if test_item.test_use == "300201":
                    dot_dict = {}
                    dot_dict["ocr_dot"] = dot["score_dot"]
                    dot_dict["cut_dot"] = dot["dot"]
                    dot_dict["ocr_height"] = dot["score_height"]
                    dot_dict["cut_height"] = dot["height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"]))
                    dot_dict["ocr_width"] = dot["score_width"]
                    dot_dict["cut_width"] = dot["width"]
                    dot_dict["type"] = "27"
                    dot_dict["img_use"] = "300201"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)
                elif test_item.test_use == "300202":
                    dot_dict = {}
                    dot_dict["ocr_dot"] = None
                    dot_dict["cut_dot"] = dot["dot"]
                    dot_dict["ocr_height"] = None
                    dot_dict["cut_height"] = dot["height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"]))
                    dot_dict["ocr_width"] = None
                    dot_dict["cut_width"] = dot["width"]
                    dot_dict["type"] = "27"
                    dot_dict["img_use"] = "300202"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)

        return page_ocr_dict

    def _make_dict_ocr(self, page_dict, pdf):
        page_ocr_dict = {}
        page_ocr_dict["width"] = page_dict["width"]
        page_ocr_dict["height"] = page_dict["height"]
        page_ocr_dict["uuid"] = str(uuid.uuid1())
        page_ocr_dict["ocr_dict"] = []
        for dot in page_dict["data"]:
            if dot["type"] == "sn":
                dot_dict = {}
                dot_dict["ocr_dot"] = dot["dot"]
                dot_dict["cut_dot"] = dot["dot"]
                dot_dict["ocr_height"] = dot["height"]
                dot_dict["index"] = None
                dot_dict["ocr_width"] = dot["width"]
                dot_dict["cut_height"] = dot["height"]
                dot_dict["cut_width"] = dot["width"]
                dot_dict["type"] = "28"
                dot_dict["img_use"] = "300201"
                dot_dict["result"] = None
                dot_dict["result_status"] = None
                dot_dict["img_path"] = None
                page_ocr_dict["ocr_dict"].append(dot_dict)
            elif dot["type"] == "no":
                dot_dict = {}
                dot_dict["ocr_dot"] = dot["dot"]
                dot_dict["cut_dot"] = dot["dot"]
                dot_dict["ocr_height"] = dot["height"]
                dot_dict["index"] = None
                dot_dict["ocr_width"] = dot["width"]
                dot_dict["cut_height"] = dot["height"]
                dot_dict["cut_width"] = dot["width"]
                dot_dict["type"] = "29"
                dot_dict["img_use"] = "300201"
                dot_dict["result"] = None
                dot_dict["result_status"] = None
                dot_dict["img_path"] = None
                page_ocr_dict["ocr_dict"].append(dot_dict)
            elif dot["type"] == "miss":
                dot_dict = {}
                dot_dict["ocr_dot"] = dot["dot"]
                dot_dict["cut_dot"] = dot["dot"]
                dot_dict["ocr_height"] = dot["height"]
                dot_dict["index"] = None
                dot_dict["ocr_width"] = dot["width"]
                dot_dict["cut_height"] = dot["height"]
                dot_dict["cut_width"] = dot["width"]
                dot_dict["type"] = "20"
                dot_dict["img_use"] = "300201"
                dot_dict["result"] = None
                dot_dict["result_status"] = None
                dot_dict["img_path"] = None
                page_ocr_dict["ocr_dict"].append(dot_dict)
            elif dot["type"] == "select":
                j = 0
                """
                dot_dict = {}
                dot_dict["ocr_dot"] = dot["dot"]
                dot_dict["cut_dot"] = dot["dot"]
                dot_dict["ocr_height"] = dot["height"]
                dot_dict["cut_height"] = dot["height"]
                dot_dict["index"] = "{0}".format(str(dot["start"] + j))
                dot_dict["ocr_width"] = dot["width"]
                dot_dict["cut_width"] = dot["width"]
                dot_dict["type"] = "21"
                dot_dict["img_use"] = "300201"
                dot_dict["result"] = None
                dot_dict["result_status"] = None
                dot_dict["img_path"] = None
                page_ocr_dict["ocr_dict"].append(dot_dict)
                """
                while j < dot["num"]:
                    dot_dict = {}
                    up = 28.339 + (j % 5) * dot["every_height"] + dot["dot"][1]
                    left = (int(j / 5)) * dot["every_width"] + dot["dot"][0]
                    dot_dict["ocr_dot"] = [left, up]
                    dot_dict["cut_dot"] = [left, up]
                    dot_dict["ocr_height"] = dot["every_height"]
                    dot_dict["cut_height"] = dot["every_height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"] + j))
                    dot_dict["ocr_width"] = dot["every_width"]
                    dot_dict["cut_width"] = dot["every_width"]
                    dot_dict["type"] = "21"
                    dot_dict["img_use"] = "300201"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)
                    j += 1
            elif dot["type"] == "multi":
                j = 0
                while j < dot["num"]:
                    dot_dict = {}
                    up = 28.339 + (j % 5) * dot["every_height"] + dot["dot"][1]
                    left = (int(j / 5)) * dot["every_width"] + dot["dot"][0]
                    dot_dict["ocr_dot"] = [left, up]
                    dot_dict["cut_dot"] = [left, up]
                    dot_dict["ocr_height"] = dot["every_height"]
                    dot_dict["cut_height"] = dot["every_height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"] + j))
                    dot_dict["ocr_width"] = dot["every_width"]
                    dot_dict["cut_width"] = dot["every_width"]
                    dot_dict["type"] = "22"
                    dot_dict["img_use"] = "300201"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)
                    j += 1
            elif dot["type"] == "judge":
                j = 0
                while j < dot["num"]:
                    dot_dict = {}
                    up = 28.339 + (j % 5) * dot["every_height"] + dot["dot"][1]
                    left = (int(j / 5)) * dot["every_width"] + dot["dot"][0]
                    dot_dict["ocr_dot"] = [left, up]
                    dot_dict["cut_dot"] = [left, up]
                    dot_dict["ocr_height"] = dot["every_height"]
                    dot_dict["cut_height"] = dot["every_height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"] + j))
                    dot_dict["ocr_width"] = dot["every_width"]
                    dot_dict["cut_width"] = dot["every_width"]
                    dot_dict["type"] = "23"
                    dot_dict["img_use"] = "300201"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)
                    j += 1
            elif dot["type"] == "fill":
                if dot["show_title"] == 1:
                    # dot["every_height"] += dot["title_height"]
                    dot["dot"][1] += dot["title_height"]
                if pdf.pdf_use == "300201":
                    dot_dict = {}
                    dot_dict["ocr_dot"] = dot["score_dot"]
                    dot_dict["cut_dot"] = dot["dot"]
                    dot_dict["ocr_height"] = dot["score_height"]
                    dot_dict["cut_height"] = dot["every_height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"]))
                    dot_dict["ocr_width"] = dot["score_width"]
                    dot_dict["cut_width"] = dot["every_width"]
                    dot_dict["type"] = "25"
                    dot_dict["img_use"] = "300201"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)
                elif pdf.pdf_use == "300202":
                    dot_dict = {}
                    dot_dict["ocr_dot"] = None
                    dot_dict["cut_dot"] = dot["dot"]
                    dot_dict["ocr_height"] = None
                    dot_dict["cut_height"] = dot["every_height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"]))
                    dot_dict["ocr_width"] = None
                    dot_dict["cut_width"] = dot["every_width"]
                    dot_dict["type"] = "25"
                    dot_dict["img_use"] = "300202"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)
            elif dot["type"] == "answer":
                if pdf.pdf_use == "300201":
                    dot_dict = {}
                    dot_dict["ocr_dot"] = dot["score_dot"]
                    dot_dict["cut_dot"] = dot["dot"]
                    dot_dict["ocr_height"] = dot["score_height"]
                    dot_dict["cut_height"] = dot["height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"]))
                    dot_dict["ocr_width"] = dot["score_width"]
                    dot_dict["cut_width"] = dot["width"]
                    dot_dict["type"] = "27"
                    dot_dict["img_use"] = "300201"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)
                elif pdf.pdf_use == "300202":
                    dot_dict = {}
                    dot_dict["ocr_dot"] = None
                    dot_dict["cut_dot"] = dot["dot"]
                    dot_dict["ocr_height"] = None
                    dot_dict["cut_height"] = dot["height"]
                    dot_dict["index"] = "{0}".format(str(dot["start"]))
                    dot_dict["ocr_width"] = None
                    dot_dict["cut_width"] = dot["width"]
                    dot_dict["type"] = "27"
                    dot_dict["img_use"] = "300202"
                    dot_dict["result"] = None
                    dot_dict["result_status"] = None
                    dot_dict["img_path"] = None
                    page_ocr_dict["ocr_dict"].append(dot_dict)

        return page_ocr_dict

    def _read_over_select_multi_judge(self, result_dict, paper, jpg_url, pdf, student_no, booklet_id, page_url,
                                      student_no_id, student_name, school_name, student_id):
        with db.auto_commit():
            score_id = str(uuid.uuid1())
            if result_dict["ocr_result_status"] == "200":
                status = 301
                png_status = 304
            else:
                status = 303
                png_status = 303
            question = j_question.query.filter(j_question.paper_id == paper.id,
                                               j_question.question_number == result_dict["index"]).first()
            # TODO 清理标签
            if result_dict["ocr_result"] in question.answerhtml:
                score = question.score
            else:
                score = 0
            png_dict = {
                "isdelete": 0,
                "createtime": datetime.now(),
                "updatetime": datetime.now(),
                "png_id": str(uuid.uuid1()),
                "png_url": jpg_url,
                "pdf_id": pdf.pdf_id,
                "png_result": result_dict["ocr_result"],
                "png_status": status,
                "png_type": result_dict["type"],
                "question": question.content,
                "booklet_id": booklet_id,
                "page_url": page_url,
                "student_no": student_no,
                "student_no_id": student_no_id,
                "student_name": student_name,
                "school": school_name,
                "result_score": score,
                "result_update": score,
                "score_id": score_id
            }
            score_dict = {
                "id": score_id,
                "student_id": student_id,
                "booklet_id": booklet_id,
                "question_id": question.id,
                "grade_by": "system-ocr",
                "question_number": result_dict["index"],
                "score": score,
                "question_url": jpg_url,
                "status": png_status
            }
            png_instance = j_answer_png.create(png_dict)
            db.session.add(png_instance)
            score_instance = j_score.create(score_dict)
            db.session.add(score_instance)

    def _read_over_fill(self, result_dict, paper, jpg_url, pdf, student_no, booklet_id, page_url,
                                      student_no_id, student_name, school_name, student_id, img_use):
        if img_use == "300201":
            # 已批阅
            score_id = str(uuid.uuid1())
            if result_dict["ocr_result_status"] == "200":
                status = 301
                png_status = 304
            else:
                status = 303
                png_status = 303
            question = j_question.query.filter(j_question.paper_id == paper.id,
                                               j_question.question_number == result_dict["index"]).first()
            # 超过分数
            if question.score < int(result_dict["ocr_result"]) or result_dict["ocr_result_status"] != "200":
                status = 303,
                png_status = 303
                score = None,
            else:
                score = int(result_dict["ocr_result"])
            png_dict = {
                "isdelete": 0,
                "createtime": datetime.now(),
                "updatetime": datetime.now(),
                "png_id": str(uuid.uuid1()),
                "png_url": jpg_url,
                "pdf_id": pdf.pdf_id,
                "png_result": result_dict["ocr_result"],
                "png_status": status,
                "png_type": result_dict["type"],
                "question": question.content,
                "booklet_id": booklet_id,
                "page_url": page_url,
                "student_no": student_no,
                "student_no_id": student_no_id,
                "student_name": student_name,
                "school": school_name,
                "result_score": result_dict["ocr_result"],
                "result_update": result_dict["ocr_result"],
                "score_id": score_id
            }
            score_dict = {
                "id": score_id,
                "student_id": student_id,
                "booklet_id": booklet_id,
                "question_id": question.id,
                "grade_by": "system-ocr",
                "question_number": result_dict["index"],
                "score": score,
                "question_url": jpg_url,
                "status": png_status
            }
        else:
            # 未批阅
            score_id = str(uuid.uuid1())

            status = 304
            png_status = 302

            question = j_question.query.filter(j_question.paper_id == paper.id,
                                               j_question.question_number == result_dict["index"]).first()
            png_dict = {
                "isdelete": 0,
                "createtime": datetime.now(),
                "updatetime": datetime.now(),
                "png_id": str(uuid.uuid1()),
                "png_url": jpg_url,
                "pdf_id": pdf.pdf_id,
                "png_result": result_dict["ocr_result"],
                "png_status": status,
                "png_type": "24",
                "question": question.content,
                "booklet_id": booklet_id,
                "page_url": page_url,
                "student_no": student_no,
                "student_no_id": student_no_id,
                "student_name": student_name,
                "school": school_name,
                "result_score": None,
                "result_update": None,
                "score_id": score_id
            }
            score_dict = {
                "id": score_id,
                "student_id": student_id,
                "booklet_id": booklet_id,
                "question_id": question.id,
                "grade_by": "system-ocr",
                "question_number": result_dict["index"],
                "score": None,
                "question_url": jpg_url,
                "status": png_status
            }
        with db.auto_commit():
            png_instance = j_answer_png.create(png_dict)
            score_instance = j_score.create(score_dict)
            db.session.add(png_instance)
            db.session.add(score_instance)

    def _read_over_answer(self, result_dict, paper, jpg_url, pdf, student_no, booklet_id, page_url,
                                      student_no_id, student_name, school_name, student_id, img_use):
        if img_use == "300201":
            # 已批阅
            score_id = str(uuid.uuid1())
            if result_dict["ocr_result_status"] == "200":
                status = 301
                png_status = 304
            else:
                status = 303
                png_status = 303
            question = j_question.query.filter(j_question.paper_id == paper.id,
                                               j_question.question_number == result_dict["index"]).first()
            # 超过分数
            if question.score < int(result_dict["ocr_result"]) or result_dict["ocr_result_status"] != "200":
                status = 303,
                png_status = 303
                score = None,
            else:
                score = int(result_dict["ocr_result"])
            png_dict = {
                "isdelete": 0,
                "createtime": datetime.now(),
                "updatetime": datetime.now(),
                "png_id": str(uuid.uuid1()),
                "png_url": jpg_url,
                "pdf_id": pdf.pdf_id,
                "png_result": result_dict["ocr_result"],
                "png_status": status,
                "png_type": result_dict["type"],
                "question": question.content,
                "booklet_id": booklet_id,
                "page_url": page_url,
                "student_no": student_no,
                "student_no_id": student_no_id,
                "student_name": student_name,
                "school": school_name,
                "result_score": result_dict["ocr_result"],
                "result_update": result_dict["ocr_result"],
                "score_id": score_id
            }

            score_dict = {
                "id": score_id,
                "student_id": student_id,
                "booklet_id": booklet_id,
                "question_id": question.id,
                "grade_by": "system-ocr",
                "question_number": result_dict["index"],
                "score": score,
                "question_url": jpg_url,
                "status": png_status
            }
        else:
            # 未批阅
            score_id = str(uuid.uuid1())
            status = 304
            png_status = 302

            question = j_question.query.filter(j_question.paper_id == paper.id,
                                               j_question.question_number == result_dict["index"]).first()
            png_dict = {
                "isdelete": 0,
                "createtime": datetime.now(),
                "updatetime": datetime.now(),
                "png_id": str(uuid.uuid1()),
                "png_url": jpg_url,
                "pdf_id": pdf.pdf_id,
                "png_result": result_dict["ocr_result"],
                "png_status": status,
                "png_type": "26",
                "question": question.content,
                "booklet_id": booklet_id,
                "page_url": page_url,
                "student_no": student_no,
                "student_no_id": student_no_id,
                "student_name": student_name,
                "school": school_name,
                "result_score": None,
                "result_update": None,
                "score_id": score_id
            }
            score_dict = {
                "id": score_id,
                "student_id": student_id,
                "booklet_id": booklet_id,
                "question_id": question.id,
                "grade_by": "system-ocr",
                "question_number": result_dict["index"],
                "score": None,
                "question_url": jpg_url,
                "status": png_status
            }
        with db.auto_commit():
            png_instance = j_answer_png.create(png_dict)
            score_instance = j_score.create(score_dict)
            db.session.add(png_instance)
            db.session.add(score_instance)


    def download_pdf(self):
        # 异步任务下载pdf
        from jinrui.models.jinrui import test_pdf
        test_item = test_pdf.query.filter(test_pdf.test_status == "300501").first()
        if test_item:
            auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
            bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)

            pdf_name = test_item.pdf_url.split("/")
            pdf_save_path = test_item.pdf_path + pdf_name[-1]
            # 存储pdf到本地
            result = bucket.get_object_to_file(pdf_name[-1], pdf_save_path)
            if result.status != 200:
                raise Exception("下载pdf失败，失败pdf_url:" + test_item.pdf_url)
            else:
                jpg_dir = self._conver_img(test_item.pdf_path, pdf_save_path, pdf_name[-1])

                current_app.logger.info(jpg_dir)

                page_ond_dict = {}
                page_two_dict = {}
                page_three_dict = {}
                page_four_dict = {}
                for page_dict in json.loads(test_item.page_list):
                    current_app.logger.info(page_dict)
                    current_app.logger.info(test_item)
                    if page_dict["page"] == 1:
                        page_ond_dict = self._make_dict(page_dict, test_item)
                    elif page_dict["page"] == 2:
                        page_two_dict = self._make_dict(page_dict, test_item)
                    elif page_dict["page"] == 3:
                        page_three_dict = self._make_dict(page_dict, test_item)
                    elif page_dict["page"] == 4:
                        page_four_dict = self._make_dict(page_dict, test_item)

                current_app.logger.info(">>>>>>>>>>>>>dict_over")
                jpg_index = 0
                page_list = []
                while jpg_index < len(jpg_dir):
                    jpg_dict = jpg_dir[jpg_index: jpg_index + 4]
                    page_one = {
                        "jpg_path": test_item.pdf_path + jpg_dict[0],
                        "json_dict": page_ond_dict
                    }
                    page_list.append(page_one)
                    page_two = {
                        "jpg_path": test_item.pdf_path + jpg_dict[1],
                        "json_dict": page_two_dict
                    }
                    page_list.append(page_two)
                    page_three = {
                        "jpg_path": test_item.pdf_path + jpg_dict[2],
                        "json_dict": page_three_dict
                    }
                    page_list.append(page_three)
                    page_four = {
                        "jpg_path": test_item.pdf_path + jpg_dict[3],
                        "json_dict": page_four_dict
                    }
                    page_list.append(page_four)

                    jpg_index += 4
                with db.auto_commit():
                    test_instance = test_item.update({
                        "test_sheet": json.dumps(page_list),
                        "test_status": "300502"
                    }, null="not")
                    db.session.add(test_instance)

        else:
            current_app.logger.info(">>>>>>>>>>>>>>need to download: 0")

    def get_pdf_dict(self):
        # 获取json结构
        args = parameter_required(("test_id", ))
        from jinrui.models.jinrui import test_pdf
        test_item = test_pdf.query.filter(test_pdf.test_id == args.get("test_id")).first_("未找到该信息")
        if test_item.test_status == "300501":
            return {
                "status": 405,
                "message": "尚未下载完毕"
            }
        else:
            return {
                "status": 200,
                "message": "获取成功",
                "data": json.loads(test_item.test_sheet)
            }


    def get_pdf(self):
        args = parameter_required(("pdf_status",))
        if args.get("pdf_status") == "300306":
            pdf = j_answer_pdf.query.filter(j_answer_pdf.isdelete == 0, j_answer_pdf.pdf_status == "300306") \
                .order_by(j_answer_pdf.createtime.desc()).first()
            if pdf:

                pdf_url = pdf.pdf_url
                pdf_uuid = str(uuid.uuid1())
                # 创建pdf存储路径
                if platform.system() == "Windows":
                    pdf_path = "D:\\jinrui_pdf\\" + pdf_uuid + "\\"
                else:
                    pdf_path = "/tmp/jinrui_pdf/" + pdf_uuid + "/"
                if not os.path.exists(pdf_path):
                    os.makedirs(pdf_path)

                from jinrui.models.jinrui import test_pdf
                test_id = str(uuid.uuid1())
                test_dict = {
                    "isdelete": 0,
                    "createtime": datetime.now(),
                    "updatetime": datetime.now(),
                    "test_id": test_id,
                    "pdf_url": pdf_url,
                    "pdf_path": pdf_path,
                    "page_list": pdf.sheet_dict,
                    "test_status": 300501,
                    "test_use": pdf.pdf_use
                }
                with db.auto_commit():
                    test_instance = test_pdf.create(test_dict)
                    db.session.add(test_instance)

                return {
                    "status": 200,
                    "message": "开始下载",
                    "test_id": test_id
                }
        elif args.get("pdf_status") == "300303":
            pdf = j_answer_pdf.query.filter(j_answer_pdf.isdelete == 0, j_answer_pdf.pdf_status == "300303") \
                .order_by(j_answer_pdf.createtime.desc()).first()
            if pdf and pdf.pdf_ip:

                pdf_url = pdf.pdf_url
                pdf_uuid = str(uuid.uuid1())
                # 创建pdf存储路径
                if platform.system() == "Windows":
                    pdf_path = "D:\\jinrui_pdf\\" + pdf_uuid + "\\"
                else:
                    pdf_path = "/tmp/jinrui_pdf/" + pdf_uuid + "/"
                if not os.path.exists(pdf_path):
                    os.makedirs(pdf_path)

                from jinrui.models.jinrui import test_pdf
                test_id = str(uuid.uuid1())
                test_dict = {
                    "isdelete": 0,
                    "createtime": datetime.now(),
                    "updatetime": datetime.now(),
                    "test_id": test_id,
                    "pdf_url": pdf_url,
                    "pdf_path": pdf_path,
                    "page_list": pdf.sheet_dict,
                    "test_status": 300501,
                    "test_use": pdf.pdf_use
                }
                with db.auto_commit():
                    test_instance = test_pdf.create(test_dict)
                    db.session.add(test_instance)
                return {
                    "status": 200,
                    "message": "开始下载",
                    "test_id": test_id
                }

    def mock_pdf(self):
        # data = parameter_required(("file", "paper_name", "pdf_use"))
        from flask import request
        file = request.files.get("file")
        data = request.form
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

        paper = j_paper.query.filter(j_paper.name == data.get("paper_name")).first_("未找到试卷")
        sheet_id = paper.sheet_id
        if not sheet_id:
            return {
                "status": 405,
                "message": "该试卷无答题卡，请先创建"
            }
        sheet = j_answer_sheet.query.filter(j_answer_sheet.id == sheet_id).first_("答题卡数据异常")
        pdf_dict = {
            "isdelete": 0,
            "createtime": datetime.now(),
            "updatetime": datetime.now(),
            "pdf_id": str(uuid.uuid1()),
            "zip_id": None,
            "pdf_use": data.get("pdf_use"),
            "paper_name": data.get("paper_name"),
            "sheet_dict": sheet.json,
            "pdf_status": "300306",
            "pdf_url": file_url,
            "pdf_address": "zip",
            "pdf_school": "杭州崇德培训学校",
            "pdf_ip": "115.198.170.61",
            "upload_id": None
        }
        with db.auto_commit():
            pdf_instance = j_answer_pdf.create(pdf_dict)
            db.session.add(pdf_instance)

        return {
            "status": 200,
            "message": "mock数据成功"
        }

    def fix_ocr_bugs(self):
        pdf = j_answer_pdf.query.filter(j_answer_pdf.isdelete == 0, j_answer_pdf.pdf_status == "300303") \
            .order_by(j_answer_pdf.createtime.desc()).first()
        with db.auto_commit():
            pdf_instance = pdf.update({
                "pdf_status": "300304"
            })
            db.session.add(pdf_instance)

        return {
            "status": 200,
            "message": "清理数据成功"
        }