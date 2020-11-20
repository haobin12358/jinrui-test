from ..control.COcr import COcr
from ..extensions.base_resource import Resource


class AOcr(Resource):
    def __init__(self):
        self.cocr = COcr()

    def get(self, ocr):
        apis = {
            'mock_question': self.cocr.mock_question,
            'mock_answer': self.cocr.mock_answer,
            "mock_ocr_response": self.cocr.mock_ocr_response,
            "deal_pdf": self.cocr.deal_pdf,
            "get_pdf": self.cocr.get_pdf,
            "mock_booklet": self.cocr.mock_booklet,
            "fix_ocr_bugs": self.cocr.fix_ocr_bugs
        }

        return apis

    def post(self, ocr):
        apis = {
            "mock_ocr_response": self.cocr.mock_ocr_response,
            "mock_pdf": self.cocr.mock_pdf
        }

        return apis
