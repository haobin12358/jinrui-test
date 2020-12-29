import os
import re
import shutil
import zipfile
import string
import random
from datetime import datetime

import imgkit
from PIL import Image
from PIL import ImageFont as imf
from PIL import ImageDraw as imd
from bs4 import BeautifulSoup
from docx import Document
from lxml import etree
import matplotlib.pyplot as plt
from flask import current_app

from jinrui.config.secret import ALIOSS_BUCKET_NAME, ALIOSS_ENDPOINT
from jinrui.extensions.error_response import ParamsError
from jinrui.extensions.register_ext import ali_oss


class CAutopic():
    oss_domain = 'https://{}.{}'.format(ALIOSS_BUCKET_NAME, ALIOSS_ENDPOINT)
    # path_wkhtmltopdf_image = r'D:\\wkhtmltopdf\\bin\\wkhtmltoimage.exe'
    # path_wkhtmltopdf_image = r'/usr/bin/wkhtmltoimage'
    # config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    # config_img = imgkit.config(wkhtmltoimage=path_wkhtmltopdf_image)
    pass_list = ["一、", "二、", "三、", "四、", "五、", "六、", "七、", "八、", "九、"]

    def upload_to_oss(self, file_data, rename=False, msg=''):
        time_now = datetime.now()
        year = str(time_now.year)
        month = str(time_now.month)
        day = str(time_now.day)
        if rename:
            shuffix = os.path.splitext(file_data)[-1]
            img_name = self.random_name(shuffix)
            current_app.logger.info('change img name {} = {}'.format(os.path.basename(file_data), img_name))
        else:
            img_name = os.path.basename(file_data)
        data = '/img/{folder}/{year}/{month}/{day}/{img_name}'.format(folder='tmp', year=year,
                                                                      month=month, day=day,
                                                                      img_name=img_name)
        if current_app.config.get('IMG_TO_OSS'):
            try:
                ali_oss.save(data=file_data, filename=data[1:])
            except Exception as e:
                current_app.logger.error(">>> {} 上传到OSS出错 : {}  <<<".format(msg, e))
                raise Exception('服务器繁忙，请稍后再试')
        return data

    @staticmethod
    def random_name(shuffix):
        myStr = string.ascii_letters + '12345678'
        res = ''.join(random.choice(myStr) for _ in range(20)) + shuffix
        return res

    @staticmethod
    def del_file(filepath):
        """
        删除某一目录下的所有文件或文件夹
        :param filepath: 路径
        :return:
        """
        # del_list = os.listdir(filepath)
        # for f in del_list:
        #     file_path = os.path.join(filepath, f)
        if os.path.isfile(filepath):
            os.remove(filepath)
        elif os.path.isdir(filepath):
            shutil.rmtree(filepath)

    def analysis_word(self, doc_path):
        html_path = self.get_html_path(doc_path)
        if not html_path:
            return {}, {}
        files = os.listdir(html_path)

        html_name = ''
        for file in files:
            shuffix = os.path.splitext(file)[-1]

            if shuffix == '.html' or shuffix == '.HTML':
                html_name = os.path.join(html_path, file)
                break

        soup = BeautifulSoup(open(html_name, encoding='utf-8'), features='html.parser')

        head = soup.head

        body = soup.body

        sub_titles = body.contents

        new_sub_titles = []

        for title in sub_titles:
            if not title:
                continue
            new_title = str(title).replace(' ', '').replace('\n', '')

            if new_title:
                new_sub_titles.append(title)
        self._change_img(new_sub_titles, html_path)

        paper_dict = self._get_paper_dict(new_sub_titles)

        paper_dict_copy = {}
        for paper in paper_dict:
            paper_dict_copy[paper] = ''.join([str(i) for i in paper_dict.get(paper)])
        img_paper_dict = self.transform_html_to_png(html_path, head, paper_dict_copy)
        current_app.logger.info('end analysis docx ')
        #
        os.remove(doc_path)
        self.del_file(html_path)

        return paper_dict_copy, img_paper_dict

    def _change_img(self, new_sub_titles, local_path):
        current_app.logger.info('satrt replace img to oss ')
        word_tag = 'img'
        img_list_all = []
        for title in new_sub_titles:
            img_list = title.find_all(word_tag)
            if img_list:
                # print(img_list)
                img_list_all.extend(img_list)

        # print(img_list_all)
        # print(len(img_list_all))
        for img in img_list_all:
            src = img['src']
            oss_path = self.upload_to_oss(os.path.join(local_path, src))

            img['src'] = self.oss_domain + oss_path
        current_app.logger.info('end replace img to oss ')

    def _get_paper_dict(self, new_sub_titles):
        point_use = "．"  # 用来区分题目的点位
        paper_dict = {}
        num_tag = ''
        word_tag = 'font'

        for content in new_sub_titles:
            font_list = content.find_all(word_tag)

            # print(font_list)
            pre_string = ''
            change_tag = True

            for font in font_list:
                # print(font)
                font_string = font.text
                if font_string and font_string.startswith(point_use):

                    if pre_string:
                        pre_string = pre_string
                        if re.match(r'^\d+$', pre_string):
                            # print(pre_string + font_string)

                            # num_tag = pre_string + point_use
                            num_tag = pre_string
                # num_ch = re.findall(r'[\u4e00-\u9fa5]{1,3}', font_string)
                for pass_char in self.pass_list:
                    if pass_char in font_string:
                        change_tag = False
                pre_string = font_string

            if not change_tag:
                continue
            if not num_tag:
                continue
            if num_tag in paper_dict:
                paper_dict[num_tag].append(content)
                # paper_dict[num_tag] =
            else:
                paper_dict[num_tag] = [content]
        return paper_dict

    def transform_html_to_png(self, local_path, head, paper_dict):
        # self.config_img.
        current_app.logger.info('start transform html to png ')
        img_paper_dict = {}
        for paper in paper_dict:
            body = paper_dict.get(paper)
            png_path = os.path.join(local_path, self.random_name('.png'))
            html_content = """
            <html>
            {}
            <body>
            {}
            </body>
            </html>
            """.format(head, body)
            imgkit.from_string(html_content, png_path)
            oss_path = self.upload_to_oss(png_path)
            img_paper_dict[paper] = self.oss_domain + oss_path
        current_app.logger.info('end transform html to png ')
        return img_paper_dict

    def get_html_path(self, docx_path):

        html_path = os.path.join(os.path.dirname(docx_path), self.random_name(''))

        try:
            os.system(r'libreoffice --invisible --convert-to html --outdir {html_path} {docx_path}'.format(
                html_path=html_path, docx_path=docx_path))
        except:
            current_app.logger.error('转化docx 到 html error ')
            return ''
        current_app.logger.info('{} get html path {}'.format(docx_path, html_path))
        return html_path
