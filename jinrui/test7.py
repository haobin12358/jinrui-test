# -*- coding: utf-8 -*-
import json
import os
import platform
import time
import sched
from datetime import datetime

import oss2
import requests
import logging

try:
    import ConfigParser
except Exception as e:
    from configparser import ConfigParser


schedule = sched.scheduler(time.time, time.sleep)

endpoint = 'oss-cn-hangzhou.aliyuncs.com'
bucket_name = 'image-jinrui'


class ScanPdf(object):
    def __init__(self):
        self.url = 'https://jinrui.sanbinit.cn/api/pdf/upload_pdf'
        self.check = 'https://jinrui.sanbinit.cn/api/pdf/get_pdf_list'
        self.token = 'https://jinrui.sanbinit.cn/api/file/get_token'
        if platform.system() == "Windows":
            self.base_dir = r"C:\jinrui_tech\\"
        else:
            self.base_dir = r"/tmp/jinrui_tech/"
        self.log = logging.getLogger(__name__)
        self.log.setLevel(level=logging.INFO)
        if not os.path.isdir(self.base_dir):
            os.makedirs(self.base_dir)
        handler = logging.FileHandler(os.path.join(self.base_dir, 'log.txt'))
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.log.addHandler(handler)
        cfg_path = os.path.join(self.base_dir, 'existfile.cfg')
        if not os.path.isfile(cfg_path):
            fd = open(cfg_path, mode="w", encoding="utf-8")
            fd.close()
        self.cf = ConfigSettings(cfg_path)
        self.filenamelist = self.cf.sections()
        self.log.info('start')

    def scan_dir(self, inc):
        # 扫描基础目录 获取pdf类型

        pdf_use_list = os.listdir(self.base_dir)
        self.log.info('get base dir {}'.format(len(pdf_use_list)))

        for pdf_use_dir in pdf_use_list:
            current_path = os.path.join(self.base_dir, pdf_use_dir)
            if not os.path.isdir(current_path):
                continue
            if pdf_use_dir == '已批阅':
                pdf_use = "300201"

            elif pdf_use_dir == '未批阅':
                pdf_use = '300202'

            else:
                continue
            self.scan_sub_dir(pdf_use, current_path)

        schedule.enter(inc, 0, self.scan_dir, (inc,))

    def scan_sub_dir(self, pdf_use, path):
        # 扫描类型目录 获取试卷
        paperlist = os.listdir(path)
        for paper in paperlist:
            current_path = os.path.join(path, paper)
            if not os.path.isdir(current_path):
                continue
            paper_name = paper
            self.scan_file(pdf_use, paper_name, current_path)

    def scan_file(self, pdf_use, paper_name, path):
        # 扫描试卷目录 获取试卷pdf
        pdf_path_list = os.listdir(path)
        for pdf in pdf_path_list:
            current_path = os.path.join(path, pdf)
            if not os.path.isfile(current_path):
                continue
            shuffix = os.path.splitext(pdf)[-1]
            shuffix = str(shuffix).lower()
            if shuffix != '.pdf':
                continue
            if current_path in self.filenamelist:
                continue
            self.upload_pdf(pdf_use, paper_name, current_path, pdf)

    def upload_pdf(self, pdf_use, paper_name, path, pdfname):
        if self.check_pdf(pdf_use, path):
            self.log.error('文件已上传')
            return
        time_now = datetime.now()
        year = str(time_now.year)
        month = str(time_now.month)
        day = str(time_now.day)
        objname = '/img/{folder}/{year}/{month}/{day}/{img_name}'.format(
            folder='pdf', year=year, month=month, day=day, img_name=pdfname)
        if not self.upload_file(objname[1:], path):
            return
        # files = {
        #     "file": (pdfname, open(path, "rb"), "application/pdf")
        # }
        oss_area = 'https://{}.{}'.format(bucket_name, endpoint)
        pdf_url = oss_area + objname
        data = {
            'pdfuse': pdf_use,
            'pdfaddress': path,
            'pdfurl': pdf_url,
            'pagername': paper_name,
        }
        try:
            response = requests.post(self.url, params=data)
            json_response = json.loads(response.content)
            if int(json_response.get('status', 0)) == 200:
                self.log.info('文件上传成功 {}'.format(json_response.get('message')))
            if int(json_response.get('code', 0)) == 200:
                self.log.error('文件上传失败 {}'.format(json_response.get('message')))
            response.close()
        except Exception as e:
            self.log.error('文件上传失败 {}'.format(e))
        finally:
            if not self.cf.cf.has_section(path):
                # 记录文件名到配置文件
                self.cf.add_selection(path)
                # 全局变量添加文件名
                self.filenamelist.append(path)
            self.log.info('文件上传完成')

    def check_pdf(self, pdfuse, pdfaddress):
        data = {
            "pdfuse": pdfuse,
            "pdfaddress": pdfaddress,
        }
        try:
            response = requests.get(self.check, params=data)
            json_response = json.loads(response.content)
            if int(json_response.get('status', 0)) == 200:
                print(json_response.get('data'))
                return json_response.get('data')
            if int(json_response.get('code', 0)) == 200:
                print(json_response.get('data'))
                return json_response.get('data')
            response.close()
        except Exception as e:
            self.log.error('pdf 校验失败 {}'.format(e))
            return True

    def upload_file(self, filename, data):
        try:
            response = requests.get("https://jinrui.sanbinit.cn/api/file/get_token")
            content = json.loads(response.content)
            token = content.get('data')
        except Exception as e:
            self.log.error('获取auth 失败 {}'.format(e))
            return False

        if not token:
            self.log.error('获取auth 失败 token 为空')
            return False
        try:
            auth = oss2.StsAuth(token['Credentials']['AccessKeyId'],
                                token['Credentials']['AccessKeySecret'],
                                token['Credentials']['SecurityToken'])
            bucket = oss2.Bucket(auth, endpoint, bucket_name)
            bucket.put_object_from_file(filename, data)
        except Exception as e:
            self.log.error('文件上传到oss 失败 {}'.format(e))
            return False

        return True


class ConfigSettings(object):
    """读取和写入配置文件"""

    def __init__(self, config_file_path='existfile.cfg'):
        self.cf = ConfigParser()

        self.config_file_path = config_file_path
        self.cf.read(self.config_file_path)

    def sections(self):
        return self.cf.sections()

    def add_selection(self, section):
        self.cf.add_section(section)
        self.write_file()

    def write_file(self):
        with open(self.config_file_path, "w") as cfg:
            self.cf.write(cfg)


sp = ScanPdf()
schedule.enter(0, 0, sp.scan_dir, (60,))
schedule.run()
