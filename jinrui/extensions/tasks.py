# -*- coding: utf-8 -*-
from flask import current_app
# from sqlalchemy import false
# from datetime import timedelta
# from jinrui.config.enums import ActivityStatus, UserActivityStatus, OrderMainStatus, CourseStatus, CouponStatus, \
#     CouponUserStatus, ProductType, ProductStatus
from jinrui.extensions.register_ext import celery, db
import requests
import os
from datetime import datetime

# def add_async_task(func, start_time, func_args, conn_id=None, queue='high_priority'):
#     """
#     添加异步任务
#     func: 任务方法名 function
#     start_time: 任务执行时间 datetime
#     func_args: 函数所需参数 tuple
#     conn_id: 要存入redis的key
#     """
#     task_id = func.apply_async(args=func_args, eta=start_time - timedelta(hours=8), queue=queue)
#     connid = conn_id if conn_id else str(func_args[0])
#     current_app.logger.info(f'add async task: func_args:{func_args} | connid: {conn_id}, task_id: {task_id}')
#     conn.set(connid, str(task_id))
#
#
# def cancel_async_task(conn_id):
#     """
#     取消已存在的异步任务
#     conn_id: 存在于redis的key
#     """
#     exist_task_id = conn.get(conn_id)
#     if exist_task_id:
#         exist_task_id = str(exist_task_id, encoding='utf-8')
#         celery.AsyncResult(exist_task_id).revoke()
#         conn.delete(conn_id)
#         current_app.logger.info(f'取消任务成功 task_id:{exist_task_id}')

@celery.task(name='ocr_fix')
def ocr_fix():
    try:
        from jinrui.control.COcr import COcr
        cocr = COcr().deal_pdf_to_jpg()
    except:
        current_app.logger.info(">>>>>>>>>>>>>>解析pdf失败")

@celery.task(name='upload_jpg')
def upload_jpg():
    try:
        from jinrui.control.COcr import COcr
        cocr = COcr().upload_jpg_json()
    except:
        current_app.logger.info(">>>>>>>>>>>>>读写json失败")

@celery.task(name='mock_booklet')
def mock_booklet():
    try:
        from jinrui.control.COcr import COcr
        cocr = COcr().deal_alljpg_in_onepdf()
    except:
        current_app.logger.info(">>>>>>>>>>>>>生成答卷失败")

@celery.task(name="deal_zip")
def deal_zip():
    try:
        from jinrui.control.CAnswer import CAnswer
        canswer = CAnswer().deal_zip()
    except:
        current_app.logger.info(">>>>>>>>>>>>处理zip失败")

@celery.task(name="download_pdf")
def download_pdf():
    try:
        from jinrui.control.COcr import COcr
        cocr = COcr().download_pdf()
    except:
        current_app.logger.info(">>>>>>>>>>>下载pdf失败")


def get_path(fold):
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

def get_fetch(path, cp):
    # if qiniu:
    #     content = requests.get(MEDIA_HOST + path)
    # else:
    content = requests.get(path)
    shuffix = os.path.splitext(path)[-1]
    filename = cp.random_name(shuffix)
    filepath = get_path('doc')
    # filedbname = os.path.join(filedbpath, filename)
    filename = os.path.join(filepath, filename)
    with open(filename, 'wb') as head:
        head.write(content.content)
    return filename

@celery.task(name='auto_setpic')
def auto_setpic():
    from jinrui.models import j_paper, j_question

    from jinrui.control.Cautopic import CAutopic
    cp = CAutopic()

    jplist = j_paper.query.filter(j_paper.encode_tag == '0').all()
    current_app.logger.info('get jplist {}'.format(len(jplist)))
    try:
        with db.auto_commit():
            update_list = []
            for jp in jplist:
                paper_dict = {}
                img_paper_dict = {}
                img_answer_dict = {}
                answer_dict = {}
                encode_tag = '1'
                if jp.doc_url:
                    current_app.logger.info('jp doc {}'.format(jp.doc_url))

                    try:
                        doc_path = get_fetch(jp.doc_url, cp)
                        paper_dict, img_paper_dict = cp.analysis_word(doc_path)
                        # current_app.logger.info(paper_dict)
                        # current_app.logger.info('get paperdict ')
                        # current_app.logger.info(img_paper_dict)
                        # current_app.logger.info('get img_paper_dict')
                    except Exception as e:
                        current_app.logger.error('解析 doc 失败 pageid = {} {}'.format(jp.id, e))
                        encode_tag = '2'
                    current_app.logger.info('jp doc over')
                if jp.answer_doc_url:
                    try:
                        answer_path = get_fetch(jp.answer_doc_url, cp)
                        answer_dict, img_answer_dict = cp.analysis_word(answer_path)
                        # current_app.logger.info(answer_dict)
                        # current_app.logger.info('get answer_dict')
                        # current_app.logger.info(img_answer_dict)
                        # current_app.logger.info('get img_answer_dict')
                    except Exception as e:
                        current_app.logger.error('解析answer 失败 pageid = {} {}'.format(jp.id, e))
                        encode_tag = '3'
                for paper_num in paper_dict:
                    question = j_question.query.filter(
                        j_question.paper_id == jp.id, j_question.question_number == paper_num).first()
                    if not question:
                        continue
                    update_dict = {
                        'content': img_paper_dict.get(paper_num),
                        'answer': img_answer_dict.get(paper_num),
                        'contenthtml': paper_dict.get(paper_num),
                        'answerhtml': answer_dict.get(paper_num)}
                    # current_app.logger.info('get update dict {}'.format(update_dict))
                    question.update(update_dict)
                    update_list.append(question)
                jp.encode_tag = encode_tag
                update_list.append(jp)
            try:
                db.session.add_all(update_list)
            except Exception as e:
                current_app.logger.error('数据更新失败 {}'.format(e))
                raise e
    except Exception as e:
        current_app.logger.info('解析试卷失败 {}'.format(e))


@celery.task(name='test_print')
def test_print():
    from datetime import datetime

    current_app.logger.info('TEST PRINT: {}'.format(datetime.now()))


if __name__ == '__main__':
    from jinrui import create_app

    app = create_app()
    with app.app_context():
        # auto_setpic()
        auto_setpic()
