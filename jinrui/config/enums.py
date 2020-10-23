# -*- coding: utf-8 -*-
from ..extensions.base_enum import Enum


class TestEnum(Enum):
    ok = 66, '成功'



class CourseStatus(Enum):
    not_start = ('未开始', 101)
    had_start = (102, '已开始')
    had_end = (103, '已结束')




if __name__ == '__main__':
    print(CourseStatus('未开始').zh_value)
