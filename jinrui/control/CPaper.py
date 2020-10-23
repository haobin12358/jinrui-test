from datetime import datetime

from ..config.enums import TestEnum
from ..extensions.success_response import Success
from ..extensions.error_response import NoQuestion, UnknownQuestionType
from ..extensions.params_validates import parameter_required
from jinrui.extensions.register_ext import db
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
        for question in question_list:
            if last_question_type != self._get_question_en(question.type) \
                    and last_question_type != "" \
                    and last_question_type in ["select", "multi", "judge"]:
                response.append(select_dict)
            if question.type == "选择题":
                now_question_type = self._get_question_en(question.type)
                if now_question_type != last_question_type:
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
                        "show_title": True
                    }
                    big_question_number = big_question_number + 1
                    start = int(question.question_number)
                    select_dict["name"] = big_question_number_dict[big_question_number] + "、" + question.type
                    select_dict["start"] = start
                else:
                    select_dict["num"] = select_dict["num"] + 1
                    select_dict["score"] = select_dict["score"] + question.score

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
                        "show_title": True
                    }
                else:
                    select_dict["num"] = select_dict["num"] + 1
                    select_dict["score"] = select_dict["score"] + question.score

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
                        "show_title": True
                    }
                else:
                    select_dict["num"] = select_dict["num"] + 1
                    select_dict["score"] = select_dict["score"] + question.score

            elif question.type == "填空题":
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
                        "show_title": True
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
                        "show_title": False
                    }
                    response.append(select_dict)

            elif question.type == "解答题":
                now_question_type = self._get_question_en(question.type)
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
                    "show_title": True
                }
                response.append(select_dict)


            else:
                select_dict = {}
                return UnknownQuestionType()

            last_question_type = self._get_question_en(question.type)

            print(question.type)
            print(response)
        if last_question_type in ["select", "multi", "judge"]:
            response.append(select_dict)

        return {
            "code": 200,
            "success": True,
            "message": "获取成功",
            "data": response
        }

    def _get_question_en(self, cn_question):
        en_question_dict = ["select", "multi", "judge", "fill", "answer"]
        ch_question_dict = ["选择题", "多选题", "判断题", "填空题", "解答题"]
        index = ch_question_dict.index(cn_question)
        return en_question_dict[index]
