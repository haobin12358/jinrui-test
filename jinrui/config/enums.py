# -*- coding: utf-8 -*-
from jinrui.extensions.base_enum import Enum


class TestEnum(Enum):
    ok = 66, '成功'



class CourseStatus(Enum):
    not_start = (101, '未开始')
    had_start = (102, '已开始')
    had_end = (103, '已结束')

# 21单选22多选23判断24填空all25填空ocr26简答all27简答ocr28sn29考号
class PngType(Enum):
    select = (21, '单选题')
    multi = (22, '多选题')
    judge = (23, '判断题')
    fill = (24, '填空题')
    fill_ocr = (25, '填空题')
    answer = (26, '解答题')
    answer_ocr = (27, '解答题')
    sn = (28, '考卷编号')
    no = (29, '考号')


if __name__ == '__main__':
    print(CourseStatus(101).zh_value)
