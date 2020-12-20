import os, uuid, oss2, shutil, json, cv2, fitz, platform, requests, re
from datetime import datetime

from ..extensions.success_response import Success
from jinrui.config.secret import ACCESS_KEY_SECRET, ACCESS_KEY_ID, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME
from jinrui.extensions.register_ext import db
from ..extensions.params_validates import parameter_required
from jinrui.models.jinrui import j_question, j_answer_pdf, j_answer_png, j_student, j_organization, j_school_network, \
    j_answer_zip, j_paper, j_score, j_answer_booklet, j_answer_upload, j_answer_sheet, j_answer_jpg
from flask import current_app

class COcr():

    def __init__(self):
        self.index_h = 1684 / 1124.52
        self.index_w = 1191 / 810.81
        self.width_less = 0
        self.height_less = 0
        self.jpg_list = []

    def _use_ocr(self, image_path, image_dict):
        model = "/root/sheet_manager_test/debug-0.2/models_0_3/"
        import sheet
        d = sheet.Detector(model)
        result_path = d.set_img_path(image_path)
        data = d.detect_sheet(json_dict=image_dict)
        if result_path:
            log_path = result_path
        else:
            log_path = ""
        return log_path

    def test_ocr(self):
        data = parameter_required(("image_dict", "image_path"))
        model = "/root/sheet_manager_test/debug-0.2/models_0_3/"
        import sheet
        d = sheet.Detector(model)
        result_path = d.set_img_path(data.get("image_path"))
        data = d.detect_sheet(json_dict=data.get("image_dict"))
        return result_path


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

    def deal_pdf_to_jpg(self):
        """
        异步任务，
        pdf转为图片，
        将图片触发ocr，
        将路径存储入数据库
        """
        pdf_list = j_answer_pdf.query.filter(j_answer_pdf.isdelete == 0, j_answer_pdf.pdf_status == "300305") \
            .order_by(j_answer_pdf.createtime.desc()).all()
        if pdf_list:
            for pdf in pdf_list:
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
                    if organization:
                        org_id = organization.id
                    else:
                        org_id = None
                        current_app.logger.info(">>>>>>>>>>>>>>该ip地址未授权,ip为:" + str(pdf.pdf_ip))
                        raise Exception("获取学校组织失败")

                    pdf_url = pdf.pdf_url
                    pdf_uuid = str(uuid.uuid1())
                    # 创建pdf存储路径
                    if platform.system() == "Windows":
                        pdf_path = "D:\\jinrui_pdf\\" + pdf_uuid + "\\"
                    else:
                        pdf_path = "/tmp/jinrui_pdf/" + pdf_uuid + "/"
                    if not os.path.exists(pdf_path):
                        os.makedirs(pdf_path)

                    current_app.logger.info(">>>>>>>>>>pdf_path:" + pdf_path)
                    auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                    bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                    pdf_name = pdf_url.split("/")
                    pdf_save_path = pdf_path + pdf_name[-1]
                    # 存储pdf到本地
                    result = bucket.get_object_to_file(pdf_name[-1], pdf_save_path)
                    current_app.logger.info(">>>>>>>>>>>>>>>oss下载pdf:" + str(result.status))
                    paper_name = pdf.paper_name
                    current_app.logger.info(">>>>>>>>>>>>>>试卷名称：" + str(paper_name))

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
                            # 开始处理
                            pdf_use = j_answer_pdf.query.filter(j_answer_pdf.pdf_id == pdf.pdf_id).first()
                            pdf_instance = pdf_use.update({
                                "pdf_status": "300304"
                            })
                            db.session.add(pdf_instance)

                        current_app.logger.info(">>>>>>>>>>>>start deal pdf to jpg>>>>>>>>>>>>>>>>>>>>>>>")
                        jpg_dir = self._conver_img(pdf_path, pdf_save_path, pdf_name[-1])
                        current_app.logger.info(jpg_dir)
                        current_app.logger.info(">>>>>>>>>>>>end deal pdf to jpg>>>>>>>>>>>>>>>>>>>>>>>>>")
                        # 创建每页的json
                        page_one_dict = {}
                        page_two_dict = {}
                        page_three_dict = {}
                        page_four_dict = {}
                        for page_dict in json.loads(pdf.sheet_dict):
                            if page_dict["page"] == 1:
                                page_one_dict = self._make_dict_ocr(page_dict, pdf)
                            elif page_dict["page"] == 2:
                                page_two_dict = self._make_dict_ocr(page_dict, pdf)
                            elif page_dict["page"] == 3:
                                page_three_dict = self._make_dict_ocr(page_dict, pdf)
                            elif page_dict["page"] == 4:
                                page_four_dict = self._make_dict_ocr(page_dict, pdf)

                        jpg_index = 0
                        # pdf总页数
                        pdf_index = len(jpg_dir)
                        while jpg_index < len(jpg_dir):
                            current_app.logger.info(">>>>>>>>>>>>>>>>第" + str(jpg_index + 1) + "页开始>>>>>>>>>>>>")
                            jpg_dict = jpg_dir[jpg_index: jpg_index + 4]
                            # oss
                            auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                            bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                            page_one_file_fullname = (pdf_path.replace("/tmp", "tmp") + jpg_dict[0]).split(".")[0]
                            page_one_ext = (pdf_path + jpg_dict[0]).split(".")[1]
                            page_one_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + \
                                           page_one_file_fullname + "." + page_one_ext
                            result_one = bucket.put_object_from_file(page_one_file_fullname + "." + page_one_ext,
                                                                 pdf_path + jpg_dict[0])
                            current_app.logger.info(">>>>>>>>>>上传oss：" + str(result_one.status))
                            if result_one.status != 200:
                                current_app.logger.info(">>>>>>>>>>>>>>>>>>>上传oss失败,页码:" + str(jpg_index + 1))
                            log_path_one = self._use_ocr(pdf_path + jpg_dict[0], page_one_dict)
                            current_app.logger.info(">>>>>>>>>>>log_path:" + log_path_one)
                            if not log_path_one:
                                current_app.logger.info(">>>>>>>>>>>>>>>未成功获取路径,页码:" + str(jpg_index + 1))
                                raise Exception(">>>>>>>>>>>>>>>未成功获取路径,页码:" + str(jpg_index + 1))
                            with db.auto_commit():
                                jpg_tect = {
                                    "isdelete": 0,
                                    "createtime": datetime.now(),
                                    "updatetime": datetime.now(),
                                    "jpg_id": str(uuid.uuid1()),
                                    "pdf_id": str(pdf.pdf_id),
                                    "pdf_index": pdf_index,
                                    "jpg_status": "300401",
                                    "jpg_dict": None,
                                    "jpg_index": jpg_index + 1,
                                    "jpg_url": page_one_url,
                                    "jpg_log_path": log_path_one
                                }
                                jpg_instance = j_answer_jpg.create(jpg_tect)
                                db.session.add(jpg_instance)

                            auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                            bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                            page_two_file_fullname = (pdf_path.replace("/tmp", "tmp") + jpg_dict[1]).split(".")[0]
                            page_two_ext = (pdf_path + jpg_dict[0]).split(".")[1]
                            page_two_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" \
                                           + page_two_file_fullname + "." + page_two_ext
                            result_two = bucket.put_object_from_file(page_two_file_fullname + "." + page_two_ext,
                                                                 pdf_path + jpg_dict[0])
                            current_app.logger.info(">>>>>>>>>>上传oss：" + str(result_two.status))
                            if result_two.status != 200:
                                current_app.logger.info(">>>>>>>>>>>>>>>>>>>上传oss失败,页码:" + str(jpg_index + 2))
                            log_path_two = self._use_ocr(pdf_path + jpg_dict[1], page_two_dict)
                            current_app.logger.info(">>>>>>>>>>>log_path:" + log_path_two)
                            if not log_path_two:
                                current_app.logger.info(">>>>>>>>>>>>>>>未成功获取路径,页码:" + str(jpg_index + 2))
                                raise Exception(">>>>>>>>>>>>>>>未成功获取路径,页码:" + str(jpg_index + 2))
                            with db.auto_commit():
                                jpg_tect = {
                                    "isdelete": 0,
                                    "createtime": datetime.now(),
                                    "updatetime": datetime.now(),
                                    "jpg_id": str(uuid.uuid1()),
                                    "pdf_id": str(pdf.pdf_id),
                                    "pdf_index": pdf_index,
                                    "jpg_status": "300401",
                                    "jpg_dict": None,
                                    "jpg_index": jpg_index + 2,
                                    "jpg_url": page_two_url,
                                    "jpg_log_path": log_path_two
                                }
                                jpg_instance = j_answer_jpg.create(jpg_tect)
                                db.session.add(jpg_instance)

                            auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                            bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                            page_three_file_fullname = (pdf_path.replace("/tmp", "tmp") + jpg_dict[2]).split(".")[0]
                            page_three_ext = (pdf_path + jpg_dict[0]).split(".")[1]
                            page_three_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" \
                                             + page_three_file_fullname + "." + page_three_ext
                            result_three = bucket.put_object_from_file(page_three_file_fullname + "." + page_three_ext,
                                                                 pdf_path + jpg_dict[0])
                            current_app.logger.info(">>>>>>>>>>上传oss：" + str(result_three.status))
                            if result_three.status != 200:
                                current_app.logger.info(">>>>>>>>>>>>>>>>>>>上传oss失败,页码:" + str(jpg_index + 3))
                            log_path_three = self._use_ocr(pdf_path + jpg_dict[2], page_three_dict)
                            current_app.logger.info(">>>>>>>>>>>log_path:" + log_path_three)
                            if not log_path_three:
                                current_app.logger.info(">>>>>>>>>>>>>>>未成功获取路径,页码:" + str(jpg_index + 3))
                                raise Exception(">>>>>>>>>>>>>>>未成功获取路径,页码:" + str(jpg_index + 3))
                            with db.auto_commit():
                                jpg_tect = {
                                    "isdelete": 0,
                                    "createtime": datetime.now(),
                                    "updatetime": datetime.now(),
                                    "jpg_id": str(uuid.uuid1()),
                                    "pdf_id": str(pdf.pdf_id),
                                    "pdf_index": pdf_index,
                                    "jpg_status": "300401",
                                    "jpg_dict": None,
                                    "jpg_index": jpg_index + 3,
                                    "jpg_url": page_three_url,
                                    "jpg_log_path": log_path_three
                                }
                                jpg_instance = j_answer_jpg.create(jpg_tect)
                                db.session.add(jpg_instance)

                            auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                            bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                            page_four_file_fullname = (pdf_path.replace("/tmp", "tmp") + jpg_dict[3]).split(".")[0]
                            page_four_ext = (pdf_path + jpg_dict[0]).split(".")[1]
                            page_four_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + page_four_file_fullname + "." + page_four_ext
                            result_four = bucket.put_object_from_file(page_four_file_fullname + "." + page_four_ext,
                                                                 pdf_path + jpg_dict[0])
                            current_app.logger.info(">>>>>>>>>>上传oss：" + str(result_four.status))
                            if result_four.status != 200:
                                current_app.logger.info(">>>>>>>>>>>>>>>>>>>上传oss失败,页码:" + str(jpg_index + 4))
                            log_path_four = self._use_ocr(pdf_path + jpg_dict[3], page_four_dict)
                            current_app.logger.info(">>>>>>>>>>>log_path:" + log_path_four)
                            if not log_path_four:
                                current_app.logger.info(">>>>>>>>>>>>>>>未成功获取路径,页码:" + str(jpg_index + 4))
                                raise Exception(">>>>>>>>>>>>>>>未成功获取路径,页码:" + str(jpg_index + 4))
                            with db.auto_commit():
                                jpg_tect = {
                                    "isdelete": 0,
                                    "createtime": datetime.now(),
                                    "updatetime": datetime.now(),
                                    "jpg_id": str(uuid.uuid1()),
                                    "pdf_id": str(pdf.pdf_id),
                                    "pdf_index": pdf_index,
                                    "jpg_status": "300401",
                                    "jpg_dict": None,
                                    "jpg_index": jpg_index + 4,
                                    "jpg_url": page_four_url,
                                    "jpg_log_path": log_path_four
                                }
                                jpg_instance = j_answer_jpg.create(jpg_tect)
                                db.session.add(jpg_instance)

                            jpg_index += 4
                        with db.auto_commit():
                            pdf_instance = pdf.update({
                                "pdf_index": len(jpg_dir),
                                "pdf_path": pdf_path
                            })
                            db.session.add(pdf_instance)
                        current_app.logger.info(">>>>>>>>>>>>pdf to png and deal ocr success>>>>>>>>>>>>")
        else:
            current_app.logger.info(">>>>>>>>>>>>>get pdf number:0")

    def upload_jpg_json(self):
        """
        异步任务
        根据路径判断是否内容存在
        30分钟内如果依旧不存在更新状态为失败
        如果存在，更新内容存入数据库
        """
        jpg_list = j_answer_jpg.query.filter(j_answer_jpg.isdelete == 0, j_answer_jpg.jpg_status == "300401").all()
        if jpg_list:
            for jpg in jpg_list:
                log_path = jpg.jpg_log_path
                if not log_path:
                    current_app.logger.info("数据库异常丢失数据")
                    raise Exception("数据库异常丢失数据")
                if not os.path.exists(log_path):
                    current_app.logger.info("路径暂不存在")
                    last_time = jpg.createtime
                    now_time = datetime.now()
                    timedelta_second = (now_time - last_time).seconds
                    if timedelta_second >= 30:
                        with db.auto_commit():
                            jpg_instance = jpg.update({
                                "updatetime": datetime.now(),
                                "jpg_status": "300404"
                            }, null="not")
                            db.session.add(jpg_instance)
                        current_app.logger.info(">>>>>>>>>>>超时")
                else:
                    with open(log_path, 'r', encoding='utf8')as fp:
                        json_dict = json.load(fp)
                    if json_dict["status"] == 200:
                        dirct = json_dict["data"]["dirct"]
                        with db.auto_commit():
                            jpg_instance = jpg.update({
                                "updatetime": datetime.now(),
                                "jpg_status": "300402",
                                "jpg_dict": json.dumps(dirct)
                            }, null="not")
                            db.session.add(jpg_instance)
                            current_app.logger.info(">>>>>>>>>>>获取算法解析数据成功,成功页码{0},总页码{1}"
                                                    .format(str(jpg.jpg_index), str(jpg.pdf_index)))

                    else:
                        with db.auto_commit():
                            jpg_instance = jpg.update({
                                "updatetime": datetime.now(),
                                "jpg_status": "300404"
                            }, null="not")
                            db.session.add(jpg_instance)
                            current_app.logger.info(">>>>>>>>>>>算法解析失败,错误码：" + str(json_dict["status"]))

        else:
            current_app.logger.info(">>>>>>>>>>>>>get jpg number:0")

    def deal_alljpg_in_onepdf(self):
        """
        异步任务
        如果某个pdf全部解析完毕
        将其转化为答卷booklet
        """
        pdf_list = j_answer_pdf.query.filter(j_answer_pdf.isdelete == 0, j_answer_pdf.pdf_status == "300304") \
            .order_by(j_answer_pdf.createtime.desc()).all()
        if pdf_list:
            for pdf in pdf_list:
                pdf_index = pdf.pdf_index
                pdf_id = pdf.pdf_id
                upload_id = pdf.upload_id
                jpg_list = j_answer_jpg.query.filter(j_answer_jpg.isdelete == 0, j_answer_jpg.pdf_id == pdf_id,
                                                     j_answer_jpg.jpg_status == "300402")\
                    .order_by(j_answer_jpg.jpg_index.asc()).all()
                if len(jpg_list) == pdf_index:
                    # 页码数对应成功，开始生成booklet及对应的png
                    current_app.logger.info(">>>>>>>>>>>>>>start create booklets and pngs>>>>>>>>>>>>>>>>>>")
                    jpg_index = 0
                    while jpg_index < pdf_index:
                        booklet_id = str(uuid.uuid1())
                        jpg_one = jpg_list[jpg_index]
                        jpg_two = jpg_list[jpg_index + 1]
                        jpg_three = jpg_list[jpg_index + 2]
                        jpg_four = jpg_list[jpg_index + 3]
                        is_miss = "302"
                        student_id = None
                        student_name = None
                        student_no = None
                        paper = None
                        sn = None
                        student_no_id = None

                        jpg_dict_one = json.loads(jpg_one.jpg_dict)
                        jpg_dict_two = json.loads(jpg_two.jpg_dict)
                        jpg_dict_three = json.loads(jpg_three.jpg_dict)
                        jpg_dict_four = json.loads(jpg_four.jpg_dict)
                        for jpg_result in jpg_dict_one:
                            if jpg_result["index"] == "-3":
                                # 试卷sn
                                sn = jpg_result["ocr_result"]
                                paper = j_paper.query.filter(j_paper.id == sn).first()
                                if paper and paper.name == pdf.paper_name:
                                    status = "301"
                                    pic_path = jpg_result["cut_img_path"]
                                    # oss
                                    auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                                    bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                                    file_fullname = pic_path.replace("/tmp", "tmp").split(".")[0]
                                    current_app.logger.info(">>>>>>>>>>>>sn_pic_path:" + str(pic_path))
                                    ext = pic_path.split(".")[-1]
                                    jpg_uuid = str(uuid.uuid1())
                                    jpg_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + \
                                              file_fullname + "-" + jpg_uuid + "." + ext
                                    result = bucket.put_object_from_file(file_fullname + "." + ext, pic_path)
                                    current_app.logger.info(">>>>>>>>>>>>>>oss result:" + str(result.status))
                                    png_id = str(uuid.uuid1())
                                    with db.auto_commit():
                                        png_instance = j_answer_png.create({
                                            "isdelete": 0,
                                            "createtime": datetime.now(),
                                            "updatetime": datetime.now(),
                                            "png_id": png_id,
                                            "png_url": jpg_url,
                                            "pdf_id": pdf.pdf_id,
                                            "png_result": sn,
                                            "png_status": status,
                                            "png_type": "28",
                                            "question": None,
                                            "booklet_id": booklet_id,
                                            "page_url": jpg_one.jpg_url,
                                            "student_no": None,
                                            "student_no_id": png_id,
                                            "student_name": None,
                                            "school": None,
                                            "result_score": None,
                                            "result_update": None,
                                            "score_id": None
                                        })
                                        db.session.add(png_instance)
                                else:
                                    current_app.logger.info("该pdf存在异常答卷，异常答卷为第{0}张，解析中止".format(str(jpg_index)))
                                    with db.auto_commit():
                                        pdf_use = j_answer_pdf.query.filter(j_answer_pdf.pdf_id == pdf.pdf_id).first()
                                        pdf_instance = pdf_use.update({
                                            "pdf_status": "300303"
                                        })
                                        db.session.add(pdf_instance)
                                        upload_id = pdf.upload_id
                                        if upload_id:
                                            upload = j_answer_upload.query.filter(
                                                j_answer_upload.id == upload_id).first()
                                            upload_instance = upload.update({
                                                "status": "解析失败"
                                            })
                                            db.session.add(upload_instance)
                                    raise Exception("答卷异常")
                            elif jpg_result["index"] == "-2":
                                # 缺考
                                if jpg_result["ocr_result"] == "1":
                                    is_miss = "301"
                            elif jpg_result["index"] == "-4":
                                # 准考证号
                                student_no = jpg_result["ocr_result"]
                                student = j_student.query.filter(j_student.student_number == student_no).first()
                                if student:
                                    status = 301
                                    student_name = student.name
                                    student_id = student.id
                                else:
                                    status = 303
                                    student_name = None
                                    student_id = None
                                pic_path = jpg_result["cut_img_path"]
                                # oss
                                auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                                bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                                file_fullname = pic_path.replace("/tmp", "tmp").split(".")[0]
                                ext = pic_path.split(".")[-1]
                                jpg_uuid = str(uuid.uuid1())
                                jpg_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + \
                                          file_fullname + "-" + jpg_uuid + "." + ext
                                result = bucket.put_object_from_file(file_fullname + "." + ext, pic_path)
                                current_app.logger.info(">>>>>>>>>>>>oss no result:" + str(result.status))
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
                                        "page_url": jpg_one.jpg_url,
                                        "student_no": student_no,
                                        "student_no_id": student_no_id,
                                        "student_name": student_name,
                                        "school": pdf.pdf_school,
                                        "result_score": None,
                                        "result_update": None,
                                        "score_id": None
                                    })

                                    db.session.add(png_instance)

                        if paper and student_no:
                            if is_miss == "301":
                                question_list = j_question.query.filter(j_question.paper_id == paper.id).all()
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
                                # 第一页
                                for result_dict in jpg_dict_one:
                                    pic_path = result_dict["cut_img_path"]
                                    # oss
                                    auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                                    bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                                    file_fullname = pic_path.replace("/tmp", "tmp").split(".")[0]
                                    ext = pic_path.split(".")[-1]
                                    jpg_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" \
                                              + file_fullname + "." + ext
                                    result = bucket.put_object_from_file(file_fullname + "." + ext,
                                                                         pic_path)
                                    current_app.logger.info("裁剪图上传oss：" + str(result.status))
                                    current_app.logger.info("裁剪图类型：" + result_dict["type"])
                                    if result_dict["type"] in ["21", "22", "23"]:
                                        self._read_over_select_multi_judge(result_dict, paper, jpg_url, pdf, student_no,
                                                                           booklet_id, jpg_one.jpg_url, student_no_id,
                                                                           student_name,
                                                                           pdf.pdf_school, student_id, jpg_one.jpg_id)
                                    if result_dict["type"] == "25":
                                        self._read_over_fill(result_dict, paper, jpg_url, pdf, student_no,
                                                             booklet_id, jpg_one.jpg_url, student_no_id, student_name,
                                                             pdf.pdf_school, student_id, pdf.pdf_use, jpg_one.jpg_id)
                                    if result_dict["type"] == "27":
                                        self._read_over_answer(result_dict, paper, jpg_url, pdf, student_no,
                                                               booklet_id, jpg_one.jpg_url, student_no_id, student_name,
                                                               pdf.pdf_school, student_id, pdf.pdf_use, jpg_one.jpg_id)

                                # 第二页
                                for result_dict in jpg_dict_two:
                                    pic_path = result_dict["cut_img_path"]
                                    # oss
                                    auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                                    bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                                    file_fullname = pic_path.replace("/tmp", "tmp").split(".")[0]
                                    ext = pic_path.split(".")[-1]
                                    jpg_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" \
                                              + file_fullname + "." + ext
                                    result = bucket.put_object_from_file(file_fullname + "." + ext,
                                                                         pic_path)
                                    current_app.logger.info("裁剪图上传oss：" + str(result.status))
                                    if result_dict["type"] in ["21", "22", "23"]:
                                        self._read_over_select_multi_judge(result_dict, paper, jpg_url, pdf, student_no,
                                                                           booklet_id, jpg_two.jpg_url, student_no_id,
                                                                           student_name,
                                                                           pdf.pdf_school, student_id, jpg_two.jpg_id)
                                    if result_dict["type"] == "25":
                                        self._read_over_fill(result_dict, paper, jpg_url, pdf, student_no,
                                                             booklet_id, jpg_two.jpg_url, student_no_id, student_name,
                                                             pdf.pdf_school, student_id, pdf.pdf_use, jpg_two.jpg_id)
                                    if result_dict["type"] == "27":
                                        self._read_over_answer(result_dict, paper, jpg_url, pdf, student_no,
                                                               booklet_id, jpg_two.jpg_url, student_no_id, student_name,
                                                               pdf.pdf_school, student_id, pdf.pdf_use, jpg_two.jpg_id)

                                # 第三页
                                for result_dict in jpg_dict_three:
                                    pic_path = result_dict["cut_img_path"]
                                    # oss
                                    auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                                    bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                                    file_fullname = pic_path.replace("/tmp", "tmp").split(".")[0]
                                    ext = pic_path.split(".")[-1]
                                    jpg_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" \
                                              + file_fullname + "." + ext
                                    result = bucket.put_object_from_file(file_fullname + "." + ext,
                                                                         pic_path)
                                    current_app.logger.info("裁剪图上传oss：" + str(result.status))
                                    if result_dict["type"] in ["21", "22", "23"]:
                                        self._read_over_select_multi_judge(result_dict, paper, jpg_url, pdf, student_no,
                                                                           booklet_id, jpg_three.jpg_url, student_no_id,
                                                                           student_name,
                                                                           pdf.pdf_school, student_id, jpg_three.jpg_id)
                                    if result_dict["type"] == "25":
                                        self._read_over_fill(result_dict, paper, jpg_url, pdf, student_no,
                                                             booklet_id, jpg_three.jpg_url, student_no_id, student_name,
                                                             pdf.pdf_school, student_id, pdf.pdf_use, jpg_three.jpg_id)
                                    if result_dict["type"] == "27":
                                        self._read_over_answer(result_dict, paper, jpg_url, pdf, student_no,
                                                               booklet_id, jpg_three.jpg_url, student_no_id, student_name,
                                                               pdf.pdf_school, student_id, pdf.pdf_use, jpg_three.jpg_id)

                                # 第四页
                                for result_dict in jpg_dict_four:
                                    pic_path = result_dict["cut_img_path"]
                                    # oss
                                    auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
                                    bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
                                    file_fullname = pic_path.replace("/tmp", "tmp").split(".")[0]
                                    ext = pic_path.split(".")[-1]
                                    jpg_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" \
                                              + file_fullname + "." + ext
                                    result = bucket.put_object_from_file(file_fullname + "." + ext,
                                                                         pic_path)
                                    current_app.logger.info("裁剪图上传oss：" + str(result.status))
                                    if result_dict["type"] in ["21", "22", "23"]:
                                        self._read_over_select_multi_judge(result_dict, paper, jpg_url, pdf, student_no,
                                                                           booklet_id, jpg_four.jpg_url, student_no_id,
                                                                           student_name,
                                                                           pdf.pdf_school, student_id, jpg_four.jpg_id)
                                    if result_dict["type"] == "25":
                                        self._read_over_fill(result_dict, paper, jpg_url, pdf, student_no,
                                                             booklet_id, jpg_four.jpg_url, student_no_id, student_name,
                                                             pdf.pdf_school, student_id, pdf.pdf_use, jpg_four.jpg_id)
                                    if result_dict["type"] == "27":
                                        self._read_over_answer(result_dict, paper, jpg_url, pdf, student_no,
                                                               booklet_id, jpg_four.jpg_url, student_no_id, student_name,
                                                               pdf.pdf_school, student_id, pdf.pdf_use, jpg_four.jpg_id)

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
                                    "url": json.dumps([jpg_one.jpg_url, jpg_two.jpg_url, jpg_three.jpg_url, jpg_four.jpg_url]),
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
                    pdf_head = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/"
                    pdf_url = pdf.pdf_url
                    pdf_name = pdf_url.repleace(pdf_head, "")
                    result = bucket.delete_object(pdf_name)
                    current_app.logger.info(">>>>>>>>>>>oss_delete:" + str(result.status))
                    current_app.logger.info(">>>>>>>>>>>delete_pdf_name" + pdf_name)

                    pdf_path = pdf.pdf_path
                    shutil.rmtree(pdf_path)
                    current_app.logger.info(">>>>>>>>>>>>>>>pdf解析成功")
                else:
                    # 页码数对应失败，1存在300404pdf废弃upload废弃，2不存在300404但是存在300401pass
                    jpg_error_list = j_answer_jpg.query.filter(j_answer_jpg.isdelete == 0, j_answer_jpg.pdf_id == pdf_id,
                                                     j_answer_jpg.jpg_status == "300404").all()
                    if jpg_error_list:
                        current_app.logger.info(">>>>>>>>>>>>some jpg handle error>>>>>>>>>>>")
                        with db.auto_commit():
                            pdf_instance = pdf.update({
                                "updatetime": datetime.now(),
                                "pdf_status": "300303"
                            })
                            db.session.add(pdf_instance)
                            upload = j_answer_upload.query.filter(j_answer_upload.id == upload_id).first()
                            upload_instance = upload.update({
                                "update_time": datetime.now(),
                                "status": "解析失败"
                            })
                            db.session.add(upload_instance)
                    else:
                        current_app.logger.info(">>>>>>>>>>>>pdf解析中,pdf id为" + str(pdf_id))
        else:
            current_app.logger.info(">>>>>>>>>>>>>need to create booklet:0")

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
                                      student_no_id, student_name, school_name, student_id, jpg_id):
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
            if not question.answerhtml:
                current_app.logger.info(">>>>>>>>>>>>>>>试卷解析失败")
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
                "jpg_id": jpg_id,
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
            current_app.logger.info(png_dict)
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
            current_app.logger.info(score_dict)
            png_instance = j_answer_png.create(png_dict)
            db.session.add(png_instance)
            score_instance = j_score.create(score_dict)
            db.session.add(score_instance)

    def _read_over_fill(self, result_dict, paper, jpg_url, pdf, student_no, booklet_id, page_url,
                                      student_no_id, student_name, school_name, student_id, img_use, jpg_id):
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
                "jpg_id": jpg_id,
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
                "jpg_id": jpg_id,
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
                                      student_no_id, student_name, school_name, student_id, img_use, jpg_id):
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
                "jpg_id": jpg_id,
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
                "jpg_id": jpg_id,
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
        data = parameter_required(("file", "paper_name", "pdf_use"))

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
            "pdf_url": data.get("file"),
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

    def set_network(self):
        from flask import request
        net_ip = request.remote_addr
        args = parameter_required(("school_name", ))
        net_dict = j_school_network.query.filter(j_school_network.net_ip == net_ip,
                                                 j_school_network.school_name == args.get("school_name")).first()
        if net_dict:
            return {
                "status": 405,
                "message": "该ip已备案"
            }
        with db.auto_commit():
            net_instance = j_school_network.create({
                "isdelete": 0,
                "createtime": datetime.now(),
                "updatetime": datetime.now(),
                "net_id": str(uuid.uuid1()),
                "net_ip": net_ip,
                "school_name": args.get("school_name")
            })
            db.session.add(net_instance)
        return {
            "status": 200,
            "message": "备案成功"
        }