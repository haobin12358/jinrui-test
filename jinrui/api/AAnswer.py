from ..control.CAnswer import CAnswer
from ..extensions.base_resource import Resource


class AAnswer(Resource):
    def __init__(self):
        self.canswer = CAnswer()

    def post(self, answer):
        apis = {
            'upload_booklet': self.canswer.upload_booklet
        }

        return apis