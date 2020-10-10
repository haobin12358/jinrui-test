# -*- coding: utf-8 -*-

from sqlalchemy import Integer, String, Text, DateTime, orm, Boolean, DATE
from FanstiBgs.extensions.base_model import Base, Column
import datetime

class j_question(Base):
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