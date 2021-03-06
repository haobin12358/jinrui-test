from ..extensions.error_response import NoQuestion, UnknownQuestionType
from ..extensions.params_validates import parameter_required
from jinrui.models.jinrui import j_question, j_paper

class CPaper():

    def get_paper_question(self):
        args = parameter_required(("paper_id"))

        paper_id = args.get("paper_id")
        paper = j_paper.query.filter(j_paper.id == paper_id).first_("未找到对应试卷")
        question_list = j_question.query.filter(j_question.paper_id == paper_id).all()
        if not question_list:
            return NoQuestion()

        response = []
        big_question_number_dict = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二", "十三"]
        big_question_number = -1
        select_dict = {}
        last_question_type = ""
        last_question_type_ch = ""
        for question in question_list:
            if last_question_type_ch != question.type \
                    and last_question_type != "" \
                    and last_question_type in ["select", "multi", "judge"]:
                response.append(select_dict)
            if question.type in ["选择题", "听力", "完形填空", "阅读理解", "任务型阅读"]:
                now_question_type = self._get_question_en(question.type)
                if question.type != last_question_type_ch:
                    select_dict = {
                        "type": self._get_question_en(question.type),
                        "name": "",
                        "num": 1,
                        "score": question.score,
                        "start": 0,
                        "dot": [46, 356],
                        "height": 0,
                        "width": 681,
                        "every_height": 0,
                        "every_width": 0,
                        "padding": 5.67,
                        "page": 1,
                        "title_height": 15.58,
                        "score_height": 4,
                        "score_width": 9,
                        "score_dot": [688.38, 271.95],
                        "show_title": 1
                    }
                    big_question_number = big_question_number + 1
                    start = int(question.question_number)
                    select_dict["name"] = big_question_number_dict[big_question_number] + "、" + question.type
                    select_dict["start"] = start
                else:
                    select_dict["num"] = select_dict["num"] + 1

            elif question.type == "多选题":
                now_question_type = self._get_question_en(question.type)
                if now_question_type != last_question_type:
                    big_question_number = big_question_number + 1
                    start = int(question.question_number)
                    select_dict = {
                        "type": self._get_question_en(question.type),
                        "name": big_question_number_dict[big_question_number] + "、" + question.type,
                        "num": 1,
                        "score": question.score,
                        "start": start,
                        "dot": [46, 356],
                        "height": 0,
                        "width": 681,
                        "every_height": 0,
                        "every_width": 0,
                        "padding": 5.67,
                        "page": 1,
                        "title_height": 15.58,
                        "score_height": 4,
                        "score_width": 9,
                        "score_dot": [688.38, 271.95],
                        "show_title": 1
                    }
                else:
                    select_dict["num"] = select_dict["num"] + 1

            elif question.type == "判断题":
                now_question_type = self._get_question_en(question.type)
                if now_question_type != last_question_type:
                    big_question_number = big_question_number + 1
                    start = int(question.question_number)
                    select_dict = {
                        "type": self._get_question_en(question.type),
                        "name": big_question_number_dict[big_question_number] + "、" + question.type,
                        "num": 1,
                        "score": question.score,
                        "start": start,
                        "dot": [46, 356],
                        "height": 0,
                        "width": 681,
                        "every_height": 0,
                        "every_width": 0,
                        "padding": 5.67,
                        "page": 1,
                        "title_height": 15.58,
                        "score_height": 4,
                        "score_width": 9,
                        "score_dot": [688.38, 271.95],
                        "show_title": 1
                    }
                else:
                    select_dict["num"] = select_dict["num"] + 1

            elif question.type in ["填空题", "实验探究题", "词汇运用", "语法填空"]:
                now_question_type = self._get_question_en(question.type)
                if question.type != last_question_type_ch:
                    big_question_number = big_question_number + 1
                    start = int(question.question_number)
                    question_type_list = j_question.query.filter(j_question.paper_id == paper_id, j_question.type == question.type).all()
                    score = 0
                    for row in question_type_list:
                        score += row.score
                    select_dict = {
                        "type": self._get_question_en(question.type),
                        "name": big_question_number_dict[big_question_number] + "、" + question.type + "（{0}分）".format(score),
                        "num": 1,
                        "score": question.score,
                        "start": start,
                        "dot": [46, 356],
                        "height": 0,
                        "width": 681,
                        "every_height": 0,
                        "every_width": 0,
                        "padding": 5.67,
                        "page": 1,
                        "title_height": 15.58,
                        "score_height": 4,
                        "score_width": 9,
                        "score_dot": [688.38, 271.95],
                        "show_title": 1,
                        "parts": "1"
                    }
                    response.append(select_dict)
                else:
                    select_dict = {
                        "type": self._get_question_en(question.type),
                        "name": big_question_number_dict[big_question_number] + "、" + question.type,
                        "num": 1,
                        "score": question.score,
                        "start": int(question.question_number),
                        "dot": [46, 356],
                        "height": 0,
                        "width": 681,
                        "every_height": 0,
                        "every_width": 0,
                        "padding": 5.67,
                        "page": 1,
                        "title_height": 15.58,
                        "score_height": 4,
                        "score_width": 9,
                        "score_dot": [688.38, 271.95],
                        "show_title": 0,
                        "parts": "1"
                    }
                    response.append(select_dict)

            elif question.type in ["解答题", "计算题", "书面表达"]:
                now_question_type = self._get_question_en(question.type)
                if question.type != last_question_type_ch:
                    big_question_number = big_question_number + 1
                start = int(question.question_number)

                select_dict = {
                    "type": self._get_question_en(question.type),
                    "name": big_question_number_dict[big_question_number] + "、" + question.type,
                    "num": 1,
                    "score": question.score,
                    "start": start,
                    "dot": [46, 356],
                    "height": 0,
                    "width": 681,
                    "every_height": 0,
                    "every_width": 0,
                    "padding": 5.67,
                    "page": 1,
                    "title_height": 15.58,
                    "score_height": 4,
                    "score_width": 9,
                    "score_dot": [688.38, 271.95],
                    "show_title": 1
                }
                response.append(select_dict)


            else:
                select_dict = {}
                return UnknownQuestionType()

            last_question_type = self._get_question_en(question.type)
            last_question_type_ch = question.type

        if last_question_type in ["select", "multi", "judge"]:
            response.append(select_dict)

        return {
            "code": 200,
            "success": True,
            "message": "获取成功",
            "data": response
        }

    def _get_question_en(self, cn_question):
        en_question_dict = ["select", "multi", "judge", "fill", "answer", "answer", "fill", "select", "select", "select",
                            "select", "fill", "fill", "answer"]
        ch_question_dict = ["选择题", "多选题", "判断题", "填空题", "解答题", "计算题", "实验探究题", "听力", "完形填空",
                            "阅读理解", "任务型阅读", "词汇运用", "语法填空", "书面表达"]
        index = ch_question_dict.index(cn_question)
        return en_question_dict[index]

    def html_to_pdf(self):
        data = parameter_required(("html_str", ))
        import imgkit, platform, os, uuid, shutil, oss2
        from jinrui.config.secret import ALIOSS_BUCKET_NAME, ALIOSS_ENDPOINT, ACCESS_KEY_ID, ACCESS_KEY_SECRET
        pdf_uuid = str(uuid.uuid1())
        if platform.system() == "Windows":
            pdf_path = "D:\\jinrui_pdf\\" + pdf_uuid + "\\"
        else:
            pdf_path = "/tmp/jinrui_pdf/" + pdf_uuid + "/"
        if not os.path.exists(pdf_path):
            os.makedirs(pdf_path)
        imgkit.from_string(data.get("html_str"), pdf_path + "pdf-" + pdf_uuid + ".pdf")

        auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
        pdf_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + "pdf-" + pdf_uuid + ".pdf"
        result = bucket.put_object_from_file("pdf-" + pdf_uuid + ".pdf", pdf_path + "pdf-" + pdf_uuid + ".pdf")

        return {
            "code": 200,
            "success": True,
            "message": "创建成功",
            "data": {
                "pdf_url": pdf_url
            }
        }
