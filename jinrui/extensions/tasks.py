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


def auto_setpic():
    from jinrui.models import j_paper
    import requests
    jplist = j_paper.query.filter(j_paper.encode_tag == '0').all()
    for jp in jplist:
        if jp.doc_url:

            data = requests.get(jp.doc_url)
            filename = str(jp.doc_url).split('/')[-1]
            # 拉取远端文件
            with open(filename, 'wb') as head:
                head.write(data.content)
            pass
            # todo 添加文档解析
        if jp.answer_doc_url:
            # todo 添加文档解析
            pass
    pass


if __name__ == '__main__':
    from jinrui import create_app

    app = create_app()
