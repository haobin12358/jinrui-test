from ..control.CFile import CFile
from ..extensions.base_resource import Resource


class AFile(Resource):
    def __init__(self):
        self.cfile = CFile()

    def post(self, file):
        apis = {
            'upload_files': self.cfile.upload_files
        }

        return apis

    def get(self, file):
        apis = {
            "get_oss_secret": self.cfile.get_oss_secret,
            "get_token": self.cfile.get_token
        }

        return apis
