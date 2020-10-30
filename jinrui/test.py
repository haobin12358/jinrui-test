# -*- coding: utf-8 -*-
import json
import os
import platform
import time
import sched

try:
    import ConfigParser
except Exception as e:
    from configparser import ConfigParser

# 初始化sched模块的scheduler类
# 第一个参数是一个可以返回时间戳的函数，第二个参数可以在定时未到达之前阻塞。
import requests
import logging

schedule = sched.scheduler(time.time, time.sleep)


# example
#
# # 被周期性调度触发的函数
# def execute_command(cmd, inc):
#     '''''
#     终端上显示当前计算机的连接情况
#     '''
#     # os.system(cmd)
#     print('hello word')
#     schedule.enter(inc, 0, execute_command, (cmd, inc))


class ScanPdf(object):
    def __init__(self):
        self.url = 'https://jinrui.sanbinit.cn/api/pdf/upload_pdf'
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
        self.cf = ConfigSettings()
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
            if pdf_use_dir == '0':
                pdf_use = "300201"

            elif pdf_use_dir == '1':
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

            self.upload_pdf(pdf_use, paper_name, current_path, pdf)

    def upload_pdf(self, pdf_use, paper_name, path, pdfname):

        files = {
            "file": (pdfname, open(path, "rb"), "application/pdf")
        }
        data = {
            'pdfuse': pdf_use,
            'pdfaddress': path,
            'pagername': paper_name,
        }
        try:
            response = requests.post(self.url, data, files=files)
            json_response = json.loads(response.content)
            if int(json_response.get('code', 0)) != 200:
                self.log.error('文件上传失败 {}'.format(json_response.get('message')))

        except Exception as e:
            self.log.error('文件上传失败 {}'.format(e))
        finally:
            # 记录文件名到配置文件
            self.cf.add_selection(path)
            self.log.info('文件上传完成')
            # 全局变量添加文件名
            self.filenamelist.append(path)


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
            print('file is closed')


def main(inc=60):
    # enter四个参数分别为：间隔事件、优先级（用于同时间到达的两个事件同时执行时定序）、被调用触发的函数，
    # 给该触发函数的参数（tuple形式）
    sp = ScanPdf()
    schedule.enter(0, 0, sp.scan_dir, (inc,))
    schedule.run()


main()
# local test
# base_bath = os.getcwd()
# cfg_path = os.path.join(base_bath, 'existfile.cfg')
# cf = ConfigSettings(cfg_path)
# list_dir = os.listdir(base_bath)
# for folder in list_dir:
#     current_path = os.path.join(base_bath, folder)
#     if os.path.isfile(current_path):
#         cf.add_selection(current_path)
