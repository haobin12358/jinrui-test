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
