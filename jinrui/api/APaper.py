from ..control.CPaper import CPaper
from ..extensions.base_resource import Resource


class APaper(Resource):
    def __init__(self):
        self.cpaper = CPaper()

    def get(self, paper):
        apis = {
            'get_paper_question': self.cpaper.get_paper_question
        }

        return apis