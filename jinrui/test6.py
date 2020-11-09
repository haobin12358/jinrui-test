import os, uuid, oss2, shutil, json, cv2, fitz, platform, requests, re
from datetime import datetime

from jinrui.config.secret import ACCESS_KEY_SECRET, ACCESS_KEY_ID, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME
from jinrui.extensions.register_ext import db
from jinrui.models.jinrui import j_question, j_answer_pdf, j_answer_png, j_student, j_organization, j_school_network, \
    j_answer_zip, j_paper, j_score, j_answer_booklet, j_answer_upload


def _get_all_org_behind_id(org_id):
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


def _conver_img(pdf_path, pdf_save_path, pdf_name):
    """
    将pdf转化为jpg
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
        pm = page.getPixmap(matrix=trans, alpha=False)
        if platform.system() == "Windows":
            pm.writePNG(pdf_path + '{0}-{1}.jpg'.format(pdf_name_without_ext, "%04d" % i))
            jpg_dir.append('{0}-{1}.jpg'.format(pdf_name_without_ext, "%04d" % i))
        else:
            pm.writePNG(pdf_path + '{0}-{1}.jpg'.format(pdf_name_without_ext, "%04d" % i))
            jpg_dir.append('{0}-{1}.jpg'.format(pdf_name_without_ext, "%04d" % i))
        i = i + 1

    return jpg_dir

def get_pdf():
    pdf = j_answer_pdf.query.filter(j_answer_pdf.isdelete == 0, j_answer_pdf.pdf_status == "300305") \
        .order_by(j_answer_pdf.createtime.desc()).first()
    if pdf and pdf.pdf_ip:
        """
        school_network = j_school_network.query.filter(j_school_network.net_ip == pdf.pdf_ip).first()
        if school_network:
            school_name = school_network.school_name
        else:
            school_name = pdf.pdf_school
        print(">>>>>>>>>>>>>>>>>>school_name:" + str(school_name))
        organization = j_organization.query.filter(j_organization.name == school_name,
                                                   j_organization.role_type == "SCHOOL").first()
        org_id = organization.id
        # 组织list，用于判断学生的组织id是否在其中，从而判断学生对应信息
        children_id_list = _get_all_org_behind_id(org_id)
        print(">>>>>>>>>>>>>>>>>children_id:" + str(children_id_list))

        upload_id = pdf.upload_id
        """

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

        if result.status != 200:
            with db.auto_commit():
                pdf_use = j_answer_pdf.query.filter(j_answer_pdf.pdf_id == pdf.pdf_id).first()
                pdf_instance = pdf_use.update({
                    "pdf_status": "300303"
                })
                db.session.add(pdf_instance)
            return
        else:
            with db.auto_commit():
                pdf_use = j_answer_pdf.query.filter(j_answer_pdf.pdf_id == pdf.pdf_id).first()
                pdf_instance = pdf_use.update({
                    "pdf_status": "300305"
                })
                db.session.add(pdf_instance)

            jpg_dir = _conver_img(pdf_path, pdf_save_path, pdf_name[-1])

            print(jpg_dir)
            print(pdf.sheet_dict)

            page_ond_dict = {}
            page_two_dict = {}
            page_three_dict = {}
            page_four_dict = {}
            for page_dict in json.loads(pdf.sheet_dict):
                print(page_dict)
                if page_dict["page"] == 1:
                    page_ond_dict = make_dict(page_dict, pdf)
                elif page_dict["page"] == 2:
                    page_two_dict = make_dict(page_dict, pdf)
                elif page_dict["page"] == 3:
                    page_three_dict = make_dict(page_dict, pdf)
                elif page_dict["page"] == 4:
                    page_four_dict = make_dict(page_dict, pdf)

            jpg_index = 0
            page_list = []
            while jpg_index < len(jpg_dir):
                jpg_dict = jpg_dir[jpg_index: jpg_index + 4]
                page_one = {
                    "jpg_path": pdf_path + jpg_dict[0],
                    "json_dict": page_ond_dict
                }
                page_list.append(page_one)
                page_two = {
                    "jpg_path": pdf_path + jpg_dict[1],
                    "json_dict": page_two_dict
                }
                page_list.append(page_two)
                page_three = {
                    "jpg_path": pdf_path + jpg_dict[2],
                    "json_dict": page_three_dict
                }
                page_list.append(page_three)
                page_four = {
                    "jpg_path": pdf_path + jpg_dict[3],
                    "json_dict": page_four_dict
                }
                page_list.append(page_four)

                jpg_index += 4
            print(json.dumps(page_list))

def make_dict(page_dict, pdf):
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
            dot_dict["img_use"] = "300203"
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
            dot_dict["img_use"] = "300203"
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
            dot_dict["img_use"] = "300203"
            dot_dict["result"] = None
            dot_dict["result_status"] = None
            dot_dict["img_path"] = None
            page_ocr_dict["ocr_dict"].append(dot_dict)
        elif dot["type"] == "select":
            j = 0
            while j < dot["num"]:
                dot_dict = {}
                up = 26.37 + (j % 5) * dot["every_height"] + dot["dot"][1]
                left = (int(j / 5)) * dot["every_width"] + dot["dot"][0]
                dot_dict["ocr_dot"] = [left, up]
                dot_dict["cut_dot"] = [left, up]
                dot_dict["ocr_height"] = dot["score_height"]
                dot_dict["cut_height"] = dot["score_height"]
                dot_dict["index"] = "{0}".format(str(dot["start"] + j))
                dot_dict["ocr_width"] = dot["score_width"]
                dot_dict["cut_width"] = dot["score_width"]
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
                up = 26.37 + (j % 5) * dot["every_height"] + dot["dot"][1]
                left = (int(j / 5)) * dot["every_width"] + dot["dot"][0]
                dot_dict["ocr_dot"] = [left, up]
                dot_dict["cut_dot"] = [left, up]
                dot_dict["ocr_height"] = dot["score_height"]
                dot_dict["cut_height"] = dot["score_height"]
                dot_dict["index"] = "{0}".format(str(dot["start"] + j))
                dot_dict["ocr_width"] = dot["score_width"]
                dot_dict["cut_width"] = dot["score_width"]
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
                up = 26.37 + (j % 5) * dot["every_height"] + dot["dot"][1]
                left = (int(j / 5)) * dot["every_width"] + dot["dot"][0]
                dot_dict["ocr_dot"] = [left, up]
                dot_dict["cut_dot"] = [left, up]
                dot_dict["ocr_height"] = dot["score_height"]
                dot_dict["cut_height"] = dot["score_height"]
                dot_dict["index"] = "{0}".format(str(dot["start"] + j))
                dot_dict["ocr_width"] = dot["score_width"]
                dot_dict["cut_width"] = dot["score_width"]
                dot_dict["type"] = "23"
                dot_dict["img_use"] = "300201"
                dot_dict["result"] = None
                dot_dict["result_status"] = None
                dot_dict["img_path"] = None
                page_ocr_dict["ocr_dict"].append(dot_dict)
                j += 1
        elif dot["type"] == "fill":
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
                dot_dict["cut_height"] = dot["every_height"]
                dot_dict["index"] = "{0}".format(str(dot["start"]))
                dot_dict["ocr_width"] = dot["score_width"]
                dot_dict["cut_width"] = dot["every_width"]
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
                dot_dict["cut_height"] = dot["every_height"]
                dot_dict["index"] = "{0}".format(str(dot["start"]))
                dot_dict["ocr_width"] = None
                dot_dict["cut_width"] = dot["every_width"]
                dot_dict["type"] = "27"
                dot_dict["img_use"] = "300202"
                dot_dict["result"] = None
                dot_dict["result_status"] = None
                dot_dict["img_path"] = None
                page_ocr_dict["ocr_dict"].append(dot_dict)

    return page_ocr_dict


if __name__ == '__main__':
    from jinrui import create_app
    app = create_app()
    with app.app_context():
        print(">>>>>>>>>>>>start>>>>>>>>>>>>>>>>")
        get_pdf()
        print(">>>>>>>>>>>>>end>>>>>>>>>>>>>>>>>")