# -*- coding: utf-8 -*-

from sqlalchemy import Integer, String, Text, DateTime, orm, Boolean, DATE
from jinrui.extensions.base_model import Base, Column

class j_paper(Base):
    """
    试卷
    """
    __tablename__ = "j_paper"
    id = Column(String(32), primary_key=True)
    name = Column(String(32), nullable=False, comment="试卷名")
    subject = Column(String(32), comment="学科")
    grade = Column(String(32), comment="总分")
    type = Column(String(1), comment="试卷类型")
    doc_url = Column(Text, comment="文档链接")
    answer_doc_url = Column(Text, comment="答案文档链接")
    encode_tag = Column(String(1), comment="解析标记")
    last_encode_time = Column(DateTime, comment="上次解析时间")
    sheet_id = Column(String(32), comment="答题卡id")
    create_time = Column(DateTime, comment="创建时间")
    update_time = Column(DateTime, comment="更新时间")
    upload_by = Column(String(32), comment="上传人id")
    year = Column(String(32), comment="年级")
    publish_name = Column(String(32), comment="出版社名称")
    edition_name = Column(String(32), comment="版册名")
    allocate_type = Column(String(1), comment="上传人是否是班主任或者教师")

class j_question(Base):
    """
    题目
    """
    __tablename__ = "j_question"
    id = Column(String(32), primary_key=True)
    paper_id = Column(String(32), comment="试卷id")
    subject = Column(String(32), comment="学科")
    content = Column(Text, comment="题干")
    answer = Column(Text, comment="答案")
    explanation = Column(Text, comment="题目解析")
    question_number = Column(String(10), comment="题号")
    type = Column(String(10), comment="题型")
    score = Column(Integer, comment="总分")
    knowledge = Column(Text, comment="考点")
    create_time = Column(DateTime)
    update_time = Column(DateTime)
    url = Column(Text)

class j_student(Base):
    """
    学生
    """
    __tablename__ = "j_student"
    id = Column(String(32), primary_key=True)
    name = Column(String(32), nullable=False, comment="姓名")
    student_number = Column(String(32), comment="学号")
    sex = Column(Integer, comment="性别")
    org_id = Column(String(32), nullable=False, comment="组织id")
    phone = Column(String(32), comment="预留手机号")
    free_number = Column(Integer, nullable=False, comment="免费次数")
    free_duration = Column(DateTime, nullable=False, comment="免费时长")
    head_image = Column(String(128), comment="头像")
    create_time = Column(DateTime, comment="创建时间")
    update_time = Column(DateTime, comment="更新时间")
    status = Column(Integer, comment="用户状态")
    qq_number = Column(String(13), comment="QQ号")

class j_answer_booklet(Base):
    """
    答卷
    """
    __tablename__ = "j_answer_booklet"
    id = Column(String(32), primary_key=True)
    paper_id = Column(String(32), nullable=False, comment="试卷id")
    student_id = Column(String(32), comment="学生id")
    status = Column(String(10), comment="批阅状态")
    score = Column(Integer, comment="总得分")
    grade_time = Column(DATE, comment="批阅完成时间")
    create_time = Column(DATE, comment="创建时间")
    update_time = Column(DATE, comment="更新时间")
    url = Column(Text, comment="oss链接")
    upload_by = Column(String(32), comment="上传人id")
    grade_num = Column(Integer, comment="已批阅数目")

class j_score(Base):
    """
    答卷题目
    """
    __tablename__ = "j_score"
    id = Column(String(32), primary_key=True)
    student_id = Column(String(32), comment="学生id")
    booklet_id = Column(String(32), nullable=False, comment="答卷id")
    question_id = Column(String(32), comment="题目id")
    score = Column(Integer, comment="得分")
    question_url = Column(Text, comment="答题图片url")
    grade_by = Column(String(32), comment="批阅人id")
    create_time = Column(DateTime, comment="创建时间")
    update_time = Column(DateTime, comment="更新时间")
    question_number = Column(Integer, comment="所在试卷的编号")
    answer = Column(String(16), comment="学生答案")