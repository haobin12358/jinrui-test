from ..control.COcr import COcr
from ..extensions.base_resource import Resource


class AOcr(Resource):
    def __init__(self):
        self.cocr = COcr()

    def post(self, ocr):
        apis = {
            'mock_ocr_response': self.cocr.mock_ocr_response
        }
        return apis