from jinrui.control.CPdfUpload import CPdfUpload
from jinrui.extensions.base_resource import Resource


class APdfUpload(Resource):
    def __init__(self):
        self.cp = CPdfUpload()

    def post(self, pdf):
        api = {
            'upload_pdf': self.cp.upload_pdf
        }
        return api

    def get(self, pdf):
        api = {
            'get_pdf_list': self.cp.get_pdf_list
        }
        return api