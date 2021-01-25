import random
import string
import time
import xlrd
from flask import current_app

from jinrui.control.Cautopic import CAutopic
from jinrui.models import j_question


class CAnalysis(CAutopic):

    def analysis_execel(self, paper, path):
        try:
            book = xlrd.open_workbook(path)
            sheet = book.sheet_by_index(0)
            n_row = sheet.nrows
            # head = ['question_number', 'type', 'knowledge', 'score']
            model_list = []
            now_time = str(time.time() // 1)

            idlist = []
            paper_id = paper.id
            grade = 0
            for i in range(1, n_row):
                jpid = self.get_id(16 - len(now_time))
                while jpid in idlist:
                    jpid = self.get_id(16 - len(now_time))

                row_data = sheet.row(i)

                model_list.append(j_question.create({
                    'id': '{}{}'.format(now_time, jpid),
                    'paper_id': paper_id,
                    'subject': paper.subject,
                    'question_number': str(int(row_data[0].value)),
                    'type': row_data[1].value,
                    'knowledge': row_data[2].value,
                    'score': int(row_data[3].value),
                }))
                idlist.append(jpid)
                grade += int(row_data[3].value)

            return model_list[:], grade
        except Exception as e:
            current_app.logger.info('analysis excel error {}'.format(e))
            raise e
        finally:
            self.del_file(path)

    @staticmethod
    def get_id(len_char):
        return "".join(random.choice(string.digits) for _ in range(16 - len_char))
