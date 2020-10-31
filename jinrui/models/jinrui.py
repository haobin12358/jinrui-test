# -*- coding: utf-8 -*-

from sqlalchemy import Integer, String, Text, DateTime, orm, Boolean, DATE
from jinrui.extensions.base_model import Base, Column
from datetime import datetime

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
    upload_id = Column(String(64), comment="答卷上传记录id")

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
    status = Column(String(10), comment="303解析失败301解析成功302未批阅304已批阅")

class j_answer_zip(Base):
    """
    答卷zip
    """
    __tablename__ = "j_answer_zip"
    isdelete = Column(Boolean, default=False, comment='是否删除')
    createtime = Column(DateTime, default=datetime.now, comment='创建时间')
    updatetime = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    zip_id = Column(String(64), primary_key=True)
    zip_url = Column(String(255), comment="zip地址", nullable=False)
    zip_upload_user = Column(String(255), comment="上传人", default="system")
    zip_status = Column(String(10), comment="300101未解析300102已解析300103解析失败")

class j_answer_pdf(Base):
    """
    答卷pdf
    """
    __tablename__ = "j_answer_pdf"
    isdelete = Column(Boolean, default=False, comment='是否删除')
    createtime = Column(DateTime, default=datetime.now, comment='创建时间')
    updatetime = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    pdf_id = Column(String(64), primary_key=True)
    zip_id = Column(String(64), comment="答卷zip，可空，存在大量的来自扫描仪文件")
    pdf_use = Column(String(10), nullable=False, comment="300201先批后扫300202先扫后批")
    paper_name = Column(String(255), nullable=False, comment="试卷名")
    sheet_dict = Column(Text, comment="答题卡json")
    pdf_status = Column(String(10), comment="300301未解析300302已解析300303解析失败300304解析中")
    pdf_url = Column(String(255), comment="pdf地址")
    pdf_address = Column(Text, comment="pdf原始地址")
    pdf_ip = Column(String(20), comment="pdf上传ip")
    pdf_school = Column(String(255), comment="pdf上传学校")
    upload_id = Column(String(64), comment="上传记录id")

class j_answer_png(Base):
    """
    答卷裁剪识别图
    """
    __tablename__ = "j_answer_png"
    isdelete = Column(Boolean, default=False, comment='是否删除')
    createtime = Column(DateTime, default=datetime.now, comment='创建时间')
    updatetime = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    png_id = Column(String(64), primary_key=True)
    png_url = Column(String(255), comment="图片url")
    pdf_id = Column(String(64), comment="扫描件id")
    png_result = Column(String(255), comment="解析结果")
    png_status = Column(String(10), comment="303待处理302已处理301已批阅")
    png_type = Column(String(10), comment="21单选22多选23判断24填空all25填空ocr26简答all27简答ocr28sn29考号")
    question = Column(Text, comment="题目")
    booklet_id = Column(String(64), comment="答卷id")
    page_url = Column(String(255), comment="该页面url")
    student_no = Column(String(20), comment="学生考号")
    student_name = Column(String(255), comment="学生姓名")
    school = Column(String(255), comment="学校名称")
    result_score = Column(Integer, comment="考卷分数", default=0)
    result_update = Column(Integer, comment="考卷分数订正", default=0)
    score_id = Column(String(64), comment="答题id")

class j_answer_upload(Base):
    """
    上传记录
    """
    __tablename__ = "j_answer_upload"
    is_delete = Column(Boolean, default=False, comment='是否删除')
    create_time = Column(DateTime, default=datetime.now, comment='创建时间')
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    id = Column(String(64), primary_key=True)
    upload_by = Column(String(255), comment="上传人")
    status = Column(String(10), nullable=False, comment="上传中/待分配/已分配/分配中/文件错误")
    url = Column(String(255), comment="上传地址")


class j_answer_sheet(Base):
    """
    答题卡
    """
    __tablename__ = "j_answer_sheet"
    id = Column(String(32), primary_key=True)
    paper_id = Column(String(32), nullable=False, comment="试卷id")
    json = Column(Text, comment="答题卡json")
    create_time = Column(DateTime, comment="创建时间")
    update_time = Column(DateTime, comment="更新时间")
    name = Column(Text, comment="答题卡名")
    url = Column(Text, comment="答题卡链接")

class j_manager(Base):
    """
    账号
    """
    __tablename__ = "j_manager"
    id = Column(String(32), primary_key=True)
    name = Column(String(128), nullable=False, comment="姓名")
    nick_name = Column(String(32), comment="昵称")
    teacher_number = Column(String(32), comment="工号")
    phone = Column(String(128), comment="手机号")
    password = Column(String(128), nullable=False, comment="密码")
    sort = Column(String(32), nullable=False, comment="排序")
    openid = Column(String(32), comment="微信openid")
    head_image = Column(String(32), comment="头像")
    create_time = Column(DateTime, comment="创建时间")
    update_time = Column(DateTime, comment="更新时间")
    status = Column(Boolean, comment="用户状态0冻结1正常")
    last_login_time = Column(DateTime)
    structures = Column(String(255))

class j_role(Base):
    """
    用户组织关联
    """
    __tablename__ = "j_role"
    id = Column(String(32), primary_key=True)
    manager_id = Column(String(32), nullable=False, comment="用户id")
    org_id = Column(String(32), nullable=False, comment="组织id")
    role_type = Column(String(10), comment="角色类型")
    course = Column(String(11), comment="教师科目类型")
    create_time = Column(DateTime, comment="创建时间")
    update_time = Column(DateTime, comment="更新时间")

class j_organization(Base):
    """
    组织表
    """
    __tablename__ = "j_organization"
    id = Column(String(32), primary_key=True)
    name = Column(String(32), nullable=False, comment="组织名称")
    sort = Column(Integer, nullable=False, comment="序号")
    parent_org_id = Column(String(32), nullable=False, comment="上级组织id")
    role_type = Column(String(10), nullable=False, comment="角色类型")
    description = Column(String(512), comment="描述")
    area_id = Column(Integer, comment="区域id")
    joint_name_one = Column(String(128), comment="冗余级联名称省市区学校")
    joint_name_two = Column(String(128), comment="冗余级联名称年级班")
    status = Column(Integer, comment="组织状态0删除1开启", nullable=False)
    parent_org = Column(String(255))

class j_school_network(Base):
    """
    学校设备管理
    """
    __tablename__ = "j_school_network"
    isdelete = Column(Boolean, default=False, comment='是否删除')
    createtime = Column(DateTime, default=datetime.now, comment='创建时间')
    updatetime = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    net_id = Column(String(64), primary_key=True)
    net_ip = Column(String(20), nullable=False, comment="固定网段")
    school_name = Column(String(255), nullable=False, comment="学校名称")
    school_position = Column(String(255), comment="设备备注")