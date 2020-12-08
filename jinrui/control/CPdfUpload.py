import os
import uuid
from datetime import datetime
import string, random
from flask import request, current_app
from sqlalchemy import false

from jinrui.config.secret import ALIOSS_BUCKET_NAME, ALIOSS_ENDPOINT
from jinrui.extensions.error_response import ParamsError
from jinrui.extensions.params_validates import parameter_required
from jinrui.extensions.register_ext import ali_oss, db
from jinrui.extensions.success_response import Success
from jinrui.models import j_answer_pdf, j_school_network, j_paper, j_answer_sheet, j_answer_upload


class CPdfUpload(object):

    def upload_pdf(self):
        # return Success()
        # file = request.files.get('file')
        # if not file:
        #     return ParamsError('文件缺失')
        data = parameter_required()
        pdf_ip = request.remote_addr
        pdf_use = data.get('pdfuse')
        pdf_url = data.get('pdfurl')
        pdf_address = data.get('pdfaddress')
        pager_name = data.get('pagername')

        existlist = j_answer_pdf.query.filter(
            j_answer_pdf.pdf_ip == pdf_ip, j_answer_pdf.pdf_use == pdf_use,
            j_answer_pdf.pdf_address == pdf_address, j_answer_pdf.isdelete == false()).all()
        if existlist:
            return ParamsError('该pdf已上传')
        school = j_school_network.query.filter(
            j_school_network.net_ip == pdf_ip, j_school_network.isdelete == false()).first_('ip 非法，请联系管理员')
        pdf_school = school.school_name
        if not pdf_school:
            return ParamsError('学校名丢失，请联系管理员处理')
        # todo  获取j_paper 的key
        sheet_dict_model = j_answer_sheet.query.join(j_paper, j_paper.sheet_id == j_answer_sheet.id).filter(
            j_paper.name == pager_name, j_paper.type == 'A').first()
        if sheet_dict_model:

            sheet_dict = sheet_dict_model.json
        else:
            sheet_dict = ''
        pdf_status = '300305'
        # filename = file.filename
        # shuffix = os.path.splitext(filename)[-1]
        # current_app.logger.info(">>>  Upload File Shuffix is {0}  <<<".format(shuffix))
        # shuffix = shuffix.lower()
        # if shuffix != '.pdf':
        #     return ParamsError('上传文件需要是pdf')

        # img_name = self.random_name(shuffix)
        # time_now = datetime.now()
        # year = str(time_now.year)
        # month = str(time_now.month)
        # day = str(time_now.day)
        # newPath = os.path.join(current_app.config['BASEDIR'], 'img', 'pdf', year, month, day)
        # if not os.path.isdir(newPath):
        #     os.makedirs(newPath)
        # newFile = os.path.join(newPath, img_name)
        # 服务器本地保存
        # file.save(newFile)
        # objname = '/img/{folder}/{year}/{month}/{day}/{img_name}'.format(
        #     folder='pdf', year=year, month=month, day=day, img_name=img_name)
        # 上传oss
        # self._upload_to_oss(newFile, objname[1:], 'pdf')
        # oss_area = 'https://{}.{}'.format(ALIOSS_BUCKET_NAME, ALIOSS_ENDPOINT)
        # pdf_url = oss_area + objname
        existupload = j_answer_pdf.query.filter(
            j_answer_pdf.isdelete == false(),
            j_answer_pdf.pdf_ip == pdf_ip,
            j_answer_pdf.pdf_use == pdf_use,
            j_answer_pdf.paper_name == pager_name).first()
        if existupload:
            upload_id = existupload.upload_id
        else:
            upload_id = str(uuid.uuid4())
        with db.auto_commit():
            pdf_dict = {
                'pdf_id': str(uuid.uuid4()),
                'pdf_use': pdf_use,
                'paper_name': pager_name,
                'sheet_dict': sheet_dict,
                'pdf_status': pdf_status,
                'pdf_url': pdf_url,
                'pdf_address': pdf_address,
                'pdf_ip': pdf_ip,
                'upload_id': upload_id,
                'pdf_school': pdf_school
            }
            current_app.logger.info("get pdf {}".format(pdf_dict))
            answer_pdf = j_answer_pdf.create(pdf_dict)
            existupload = j_answer_upload.query.filter(
                j_answer_upload.is_delete == false(), j_answer_upload.id == upload_id).first()
            if not existupload:
                upload = j_answer_upload.create({
                    'id': upload_id,
                    'upload_by': pdf_school,
                    'status': '处理中',
                    'url': pdf_url
                })
                db.session.add(upload)
            db.session.add(answer_pdf)

        current_app.logger.info('success')
        return Success('上传成功')

    def get_pdf_list(self):
        data = parameter_required()
        pdf_ip = request.remote_addr
        pdf_use = data.get('pdfuse')
        pdf_address = data.get('pdfaddress')
        school = j_school_network.query.filter(
            j_school_network.net_ip == pdf_ip, j_school_network.isdelete == false()).first()
        # pdf_school = school.school_name
        msg = '文件正常'
        if not school:
            current_app.logger.error('ip 非法，请联系管理员')
            msg = 'ip 非法，请联系管理员'
            return Success(msg, data=True)

        existlist = j_answer_pdf.query.join(j_school_network, j_school_network.net_ip == j_answer_pdf.pdf_ip).filter(
            j_answer_pdf.pdf_ip == pdf_ip, j_answer_pdf.pdf_use == pdf_use, j_school_network.isdelete == false(),
            j_answer_pdf.pdf_address == pdf_address, j_answer_pdf.isdelete == false()).all()
        if existlist:
            msg = '文件已上传'
            current_app.logger.error('文件已上传')

        return Success(msg, data=bool(existlist))

    @staticmethod
    def random_name(shuffix):

        myStr = string.ascii_letters + '12345678'
        res = ''.join(random.choice(myStr) for _ in range(20)) + shuffix
        return res

    def _upload_to_oss(self, file_data, data, msg):

        if current_app.config.get('IMG_TO_OSS'):
            try:
                ali_oss.save(data=file_data, filename=data)
                current_app.logger.info('上传oss 成功 path = {}'.format(file_data))
            except Exception as e:
                current_app.logger.error(">>> {} 上传到OSS出错 : {}  <<<".format(msg, e))
                raise Exception('服务器繁忙，请稍后再试')
