# -*- coding: utf-8 -*-
from flask import current_app
from sqlalchemy import false
from datetime import timedelta
# from jinrui.config.enums import ActivityStatus, UserActivityStatus, OrderMainStatus, CourseStatus, CouponStatus, \
#     CouponUserStatus, ProductType, ProductStatus
from jinrui.extensions.register_ext import celery, db, conn


def add_async_task(func, start_time, func_args, conn_id=None, queue='high_priority'):
    """
    添加异步任务
    func: 任务方法名 function
    start_time: 任务执行时间 datetime
    func_args: 函数所需参数 tuple
    conn_id: 要存入redis的key
    """
    task_id = func.apply_async(args=func_args, eta=start_time - timedelta(hours=8), queue=queue)
    connid = conn_id if conn_id else str(func_args[0])
    current_app.logger.info(f'add async task: func_args:{func_args} | connid: {conn_id}, task_id: {task_id}')
    conn.set(connid, str(task_id))


def cancel_async_task(conn_id):
    """
    取消已存在的异步任务
    conn_id: 存在于redis的key
    """
    exist_task_id = conn.get(conn_id)
    if exist_task_id:
        exist_task_id = str(exist_task_id, encoding='utf-8')
        celery.AsyncResult(exist_task_id).revoke()
        conn.delete(conn_id)
        current_app.logger.info(f'取消任务成功 task_id:{exist_task_id}')


@celery.task(name='auto_setpic')
def auto_setpic():
    from jinrui.models import j_paper, j_question
    import requests
    import os
    from datetime import datetime
    from ..control.Cautopic import CAutopic
    cp = CAutopic()

    def _get_path(fold):
        """获取服务器上文件路径"""
        time_now = datetime.now()
        year = str(time_now.year)
        month = str(time_now.month)
        day = str(time_now.day)
        filepath = os.path.join(current_app.config['BASEDIR'], 'img', fold, year, month, day)
        # file_db_path = os.path.join('/img', fold, year, month, day)
        if not os.path.isdir(filepath):
            os.makedirs(filepath)
        return filepath

    def _get_fetch(path):
        # if qiniu:
        #     content = requests.get(MEDIA_HOST + path)
        # else:
        content = requests.get(path)

        filename = cp.random_name('.pdf')

        filepath = _get_path('pdf')
        # filedbname = os.path.join(filedbpath, filename)
        filename = os.path.join(filepath, filename)
        with open(filename, 'wb') as head:
            head.write(content.content)
        return filename

    jplist = j_paper.query.filter(j_paper.encode_tag == '0').all()

    try:
        with db.auto_commit():
            update_list = []
            for jp in jplist:
                paper_dict = {}
                answer_dict = {}
                if jp.doc_url:
                    doc_path = _get_fetch(jp.doc_url)
                    paper_dict = cp.transfordoc(doc_path)

                if jp.answer_doc_url:
                    answer_path = _get_fetch(jp.answer_doc_url)
                    answer_dict = cp.transfordoc(answer_path)
                for paper_num in paper_dict:
                    question = j_question.query.filter(
                        j_question.paper_id == jp.id, j_question.question_number == paper_num).first()
                    if not question:
                        continue
                    question.update({'content': paper_dict.get(paper_num), 'answer': answer_dict.get(paper_num)})
                    update_list.append(question)
            db.session.add_all(update_list)
    except Exception as e:
        current_app.logger.info('解析试卷失败 {}'.format(e))


if __name__ == '__main__':
    from jinrui import create_app

    app = create_app()
