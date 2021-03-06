from ..control.CAnswer import CAnswer
from ..extensions.base_resource import Resource


class AAnswer(Resource):
    def __init__(self):
        self.canswer = CAnswer()

    def post(self, answer):
        apis = {
            'upload_booklet': self.canswer.upload_booklet,
            "update_score": self.canswer.update_score
        }

        return apis

    def get(self, answer):
        apis = {
            "get_answer_list": self.canswer.get_answer_list,
            "deal_zip": self.canswer.deal_zip,
            "delete_upload": self.canswer.delete_upload
        }

        return apis