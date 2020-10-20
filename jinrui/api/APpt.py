from ..control.CPpt import CPpt
from ..extensions.base_resource import Resource


class APpt(Resource):
    def __init__(self):
        self.cppt = CPpt()

    def get(self, ppt):
        apis = {
            'get_wrong_paper_ppt': self.cppt.get_wrong_paper_ppt
        }

        return apis
