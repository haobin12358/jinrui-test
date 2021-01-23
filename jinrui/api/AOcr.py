from ..control.COcr import COcr
from ..extensions.base_resource import Resource


class AOcr(Resource):
    def __init__(self):
        self.cocr = COcr()

    def get(self, ocr):
        apis = {
            "get_pdf": self.cocr.get_pdf,
            "fix_ocr_bugs": self.cocr.fix_ocr_bugs,
            "get_pdf_dict": self.cocr.get_pdf_dict,
            "download_pdf": self.cocr.download_pdf,
            "set_network": self.cocr.set_network,
            "upload_jpg_json": self.cocr.upload_jpg_json,
            "deal_pdf_to_jpg": self.cocr.deal_pdf_to_jpg
        }

        return apis

    def post(self, ocr):
        apis = {
            "mock_pdf": self.cocr.mock_pdf,
            "test_ocr": self.cocr.test_ocr,
            "api_upload_jpg_json": self.cocr.api_upload_jpg_json
        }

        return apis
