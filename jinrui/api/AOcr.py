from ..control.COcr import COcr
from ..extensions.base_resource import Resource


class AOcr(Resource):
    def __init__(self):
        self.cocr = COcr()

    def get(self, ocr):
        apis = {
            'mock_question': self.cocr.mock_question,
            'mock_answer': self.cocr.mock_answer,
            "mock_ocr_response": self.cocr.mock_ocr_response
        }

        return apis
