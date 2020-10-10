from datetime import datetime

from ..config.enums import TestEnum
from ..extensions.success_response import Success


class COcr(object):

    def mock_ocr_response(self):

        return Success(message="获取结果成功")
