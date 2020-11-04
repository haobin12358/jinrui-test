import os
import re
import shutil
import zipfile
import string
import random
from datetime import datetime

from PIL import Image
from PIL import ImageFont as imf
from PIL import ImageDraw as imd
from docx import Document
from lxml import etree
import matplotlib.pyplot as plt
from flask import current_app

from jinrui.extensions.error_response import ParamsError
from jinrui.extensions.register_ext import ali_oss


class CAutopic():
    oss_domain = 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com'

    def transfordoc(self, filepath):
        current_app.logger.info('get path {}'.format(filepath))
        path = filepath

        shuffix = os.path.splitext(filepath)[-1]
        if shuffix != '.docx':
            return {}
        new_tmp_name = self.random_name(shuffix)
        path2 = os.path.join(os.path.dirname(filepath), new_tmp_name)
        path3 = os.path.join(os.path.dirname(filepath), '.'.join(new_tmp_name.split('.')[:-1]) + '.zip')
        shutil.copyfile(path, path2)
        os.rename(path2, path3)
        current_app.logger.info('get path3 {}'.format(path3))
        try:
            zip_file = zipfile.ZipFile(path3)
        except Exception as e:
            current_app.logger.info('解析docx 失败 {}'.format(e))
            return {}

        if os.path.isdir(path3 + "_files"):
            pass
        else:
            os.mkdir(path3 + "_files")
        for names in zip_file.namelist():
            zip_file.extract(names, path3 + "_files/")
        zip_file.close()

        # 本来用于上传oss的，需要重写
        # header = {
        #     "token": "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxMzAyNTkxMzMxNzcxNzQ4MzUyIiwiaWF0IjoxNjAyNTY1NDUwLCJleHAiOjE2MDI2NTE4NTB9.HO0k0uePIIXd0-pxh2nJAK8NJvNNmQdqsMz_3ZprAzg_uk6nb3hCX-w_RlmXpIzV_o-uDRovIRe5_DbFgQdp3A"
        # }
        # url = "https://api.jinrui.sanbinit.cn/file/upload"

        # 获取原word文档的内容
        doc = Document(path)
        doc_xml = doc._body._element.xml
        # 获取资源id对应关系
        doc_rels = doc.part._rels
        rId_list = list(doc_rels)
        current_app.logger.info(rId_list)
        current_app.logger.info(len(rId_list))
        target_list = []

        for rel in doc_rels:
            rel = doc_rels[rel]
            target_list.append(rel.target_ref)
            if "image" in rel.target_ref:
                img_name = re.findall("/(.*)", rel.target_ref)[0]

        # 转化lxml结点
        body_xml = etree.fromstring(doc_xml)  # 转换成lxml结点
        current_app.logger.info(target_list)
        current_app.logger.info(len(target_list))
        i = 0
        paper_num = 0
        paper_dict = {}
        # 遍历lxml
        while i < len(body_xml):
            # current_app.logger.info("第{0}行".format(str(i + 1)))
            # 调试用的无视
            if i == 2222:
                current_app.logger.info(str(etree.tounicode(body_xml[i])))
            # 讲需要的内容过滤成正则的对子
            in_text = self.whichin(str(etree.tounicode(body_xml[i])))
            # 增加文字格式额外条件
            if "</w:instrText>" in in_text or "</w:t>":
                in_text.append("<w:vertAlign")
                in_text.append("/>")
            # 如果条件是空或者不是对子，定义正则规则
            if not len(in_text) or len(in_text) % 2 != 0:
                re_str = "<w:r>|</w:r>"
            else:
                re_str = "<w:r>|</w:r>"
                # 如果存在eq域
                if "</w:instrText>" in in_text:
                    re_str = re_str + """|<w:fldChar w:fldCharType="begin"/>""" + """|<w:fldChar w:fldCharType="end"/>"""
                j = 0
                while j < len(in_text):
                    if re_str:
                        re_str = re_str + "|"
                    re_str = re_str + in_text[j] + ".*?" + in_text[j + 1]
                    j = j + 2
            # if i == 17:
            # print(etree.tounicode(body_xml[i]))
            # 如果存在表格
            if "<w:tbl " in str(etree.tounicode(body_xml[i])):
                re_str = re_str + """|<w:tbl """
            if "<w:tr>" in str(etree.tounicode(body_xml[i])):
                re_str = re_str + """|<w:tr>"""
            if "</w:tr>" in str(etree.tounicode(body_xml[i])):
                re_str = re_str + """|</w:tr>"""
            if "<w:tc>" in str(etree.tounicode(body_xml[i])):
                re_str = re_str + """|<w:tc>"""
            if "</w:tc>" in str(etree.tounicode(body_xml[i])):
                re_str = re_str + """|</w:tc>"""
            if "</w:tbl>" in str(etree.tounicode(body_xml[i])):
                re_str = re_str + """|</w:tbl>"""
            # 正则解析
            if re_str:
                use_list = re.findall(r"{0}".format(re_str), str(etree.tounicode(body_xml[i])))
            else:
                use_list = []
            use_str = ""
            index = 0
            # 处理上角标和下角标
            while index < len(use_list):
                if index + 3 < len(use_list):
                    if use_list[index] == "<w:r>" and use_list[index + 1] == """<w:vertAlign w:val="superscript"/>""":
                        use_list[index] = "<sup>"
                        use_list[index + 1] = ""
                        use_list[index + 3] = "</sup>"
                    if use_list[index] == "<w:r>" and use_list[index + 1] == """<w:vertAlign w:val="subscript"/>""":
                        use_list[index] = "<sub>"
                        use_list[index + 1] = ""
                        use_list[index + 3] = "</sub>"
                # 处理无效标记
                use_str = use_str + use_list[index].replace("<w:t>", "").replace("</w:t>", "").replace(
                    """<w:t xml:space="preserve">""", "")
                index = index + 1
            # 处理无效标记
            use_str = use_str.replace("<w:r>", "").replace("</w:r>", "").replace("\u3000", "")
            # 处理图片
            if "<a:blip" in use_str:
                for rId in rId_list:
                    """<a:blip r:embed="rId5" cstate="print">"""
                    if """<a:blip r:embed="{0}"/>""".format(rId) in use_str:
                        match_str = """<a:blip r:embed="{0}"/>""".format(rId)
                        use_str = self.replace_img(target_list, rId_list, rId, use_str, path3, match_str)
                    elif """<a:blip r:embed="{0}">""".format(rId) in use_str:
                        match_str = """<a:blip r:embed="{0}">""".format(rId)
                        use_str = self.replace_img(target_list, rId_list, rId, use_str, path3, match_str)
                    elif """<a:blip r:embed="{0}" cstate="print">""".format(rId) in use_str:
                        match_str = """<a:blip r:embed="{0}" cstate="print">""".format(rId)
                        use_str = self.replace_img(target_list, rId_list, rId, use_str, path3, match_str)
            # 用于临时处理eq域可先注释掉
            use_str = use_str.replace("<w:instrText>", "").replace("</w:instrText>", "") \
                .replace("""<w:instrText xml:space="preserve">""", "")
            if '<w:fldChar w:fldCharType="begin"/>' in use_str:
                current_app.logger.info(use_str)
                tmp_use_str = use_str
                start_str = '<w:fldChar w:fldCharType="begin"/>'
                start_index = use_str.index(start_str)
                end_str = '<w:fldChar w:fldCharType="end"/>'
                end_index = use_str.index(end_str)

                eq_list = re.findall(
                    r'''<w:fldChar w:fldCharType="begin"/>eq (.*?)<w:fldChar w:fldCharType="end"/>''', use_str)
                # use_str = ''
                for eq_index, _ in enumerate(eq_list):
                    img_name = self.random_name('.png')
                    time_now = datetime.now()
                    year = str(time_now.year)
                    month = str(time_now.month)
                    day = str(time_now.day)
                    newPath = os.path.join(current_app.config['BASEDIR'], 'img', 'tmp', year, month, day)
                    if not os.path.isdir(newPath):
                        os.makedirs(newPath)
                    newFile = os.path.join(newPath, img_name)
                    eq_str = self.draw_pic(tmp_use_str, newFile, eq_index)
                    if not eq_str:
                        db_path = '{domain}/img/{folder}/{year}/{month}/{day}/{img_name}'.format(domain=self.oss_domain,
                                                                                                 folder='tmp', year=year,
                                                                                                 month=month, day=day,
                                                                                                 img_name=img_name)
                        # new_eq_str = "<img src='{0}'></img>".format(db_path)
                        # img_eq = Image.open(newFile)
                        # x, y = img_eq.size
                        # high = 35
                        # width = y / (x / high)
                        new_eq_str = """<img src="{0}"  width={1}></img>""".format(db_path, "35")
                        current_app.logger.info(new_eq_str)
                    else:
                        new_eq_str = eq_str

                    use_str = use_str[:start_index] + new_eq_str + use_str[end_index + len(end_str):]
                    try:
                        start_index = use_str.index(start_str, end_index)
                        end_index = use_str.index(end_str, start_index)
                    except:
                        start_index = start_index
                        end_index = end_index

            # 处理表格
            use_str = use_str \
                .replace("<w:tbl ", """<table border="1">""") \
                .replace("<w:tr>", "<tr>") \
                .replace("<w:tc>", "<td>") \
                .replace("</w:tc>", "</td>") \
                .replace("</w:tr>", "</tr>") \
                .replace("</w:tbl>", "</table>")
            # current_app.logger.info(use_str)
            point_use = "．"  # 用来区分题目的点位
            # point_use = "."
            # 题目标号
            if (str(paper_num + 1) + point_use) in use_str:
                paper_num = paper_num + 1
            point_icon = str(paper_num) + point_use
            # 用于判断大题序号进行过滤
            pass_list = ["一、", "二、", "三、", "四、", "五、", "六、", "七、", "八、", "九、"]
            for row in pass_list:
                if row in use_str and point_icon not in use_str:
                    use_str = ""
            # 封装json，key为题号，value为题目
            if point_icon in use_str or str(paper_num) in paper_dict.keys():
                if str(paper_num) in paper_dict.keys():
                    paper_dict[str(paper_num)] = paper_dict[str(paper_num)] + "<div>" + use_str + "</div>"
                else:
                    paper_dict[str(paper_num)] = "<div>" + use_str + "</div>"
            i = i + 1
        # current_app.logger.info(paper_dict)
        # os.remove(path2)
        os.remove(path3)
        self.del_file(path3 + "_files")
        # os.removedirs(path3+"_files")
        return paper_dict

    def replace_img(self, target_list, rId_list, rId, use_str, path3, match_str):
        target_list_dict = target_list[rId_list.index(rId)].split("/")
        current_app.logger.info(use_str)
        current_app.logger.info(">>>>>>>>>>>target_dict:" + str(target_list_dict))
        if len(target_list_dict) > 1:
            current_app.logger.info(">>>>>>>>>>target_list_dict:" + str(target_list_dict))
            # picture_path = path3 + "_files\\word" + "\\" + target_list_dict[0] + "\\" + \
            #                target_list_dict[1]
            picture_path = os.path.join(path3 + "_files", 'word', target_list_dict[0], target_list_dict[1])
            url_response = self.upload_to_oss(picture_path, rename=True)
            # files = {
            #     "file": (target_list_dict[1], open(r"{0}".format(picture_path), "rb"), "image/png")
            # }
            # response = requests.post(headers=header, files=files, url=url)
            # json_response = json.loads(response.content)
            # url_response = json_response["data"]["url"]
            # print(">>>>>>>>>>>>>>>>>>url_response:" + str(url_response))
            use_str = use_str.replace(
                match_str, """<img src="{0}" height="60"></img>""".format(self.oss_domain + url_response))
        else:
            use_str = use_str.replace(match_str, """<img src="{0}" height="60"></img>""".format(
                str(target_list[rId_list.index(rId)])))
        return use_str

    @staticmethod
    def get_eqcontent(str_eq, index):
        # 获取解析字符串
        try:
            eqcontent = re.findall(
                r'''<w:fldChar w:fldCharType="begin"/>eq (.*?)<w:fldChar w:fldCharType="end"/>''', str_eq)
            current_app.logger.info(eqcontent)
            return eqcontent[int(index)]
        except:
            raise Exception('数据异常')

    def draw_pic(self, deaL_str, file_path, index=0, img_size=[]):
        if not img_size:
            img_size = [1, 1]
        eq_str = self.get_eqcontent(deaL_str, index)
        return self.switch_draw(eq_str, img_size, file_path=file_path)

    def switch_draw(self, eq_str, img_size, file_path):

        if eq_str.startswith('\\b'):
            draw_str = self.split_b(eq_str, file_path, img_size)
            if draw_str:
                draw_str = '${}$'.format(draw_str)
        elif eq_str.startswith('\\f('):
            draw_str = self.split_f(eq_str, file_path, img_size)
            if draw_str:
                draw_str = '${}$'.format(draw_str)
        elif eq_str.startswith('\\r'):
            draw_str = self.split_r(eq_str, file_path, img_size)
            if draw_str:
                draw_str = '${}$'.format(draw_str)
        elif eq_str.startswith('\\o'):
            self.split_o(eq_str, file_path=file_path)
            draw_str = False
        elif eq_str.startswith('\\s'):
            dealstr = self.deal_s(eq_str)
            return dealstr
            draw_str = False
        else:
            draw_str = self.replace_item(eq_str)
            draw_str = self.replace_sign(draw_str)
            if draw_str:
                draw_str = '${}$'.format(draw_str)
        # dd = draw_pic(e)
        current_app.logger.info(draw_str)
        if not draw_str:
            return False
        current_app.logger.info(img_size)
        if len(draw_str) >= 36:
            img_size[0] = img_size[0] + (len(draw_str) // 36) * 0.5
        current_app.logger.info(img_size)

        self.formula2img(draw_str, file_path, img_size=img_size, font_size=64)
        self.upload_to_oss(file_path, rename= False, msg='eq域')
        return False

    def split_o(self, str_eq, file_path):
        r"""\o(=, \s\up7(点燃)) """
        index_r = 0
        brac_eq = self.get_brac_dict(str_eq)
        r_list = re.findall(r'\\o', str_eq)
        # new_str_sub_list = []
        for _ in r_list:

            index_r = str_eq.index(r'\o', index_r)
            f_start = 0
            f_end = 0
            for brac in brac_eq:
                if int(brac) > int(index_r):
                    f_start = int(brac)
                    f_end = int(brac_eq.get(brac))
                    break
            self.deal_o(str_eq[f_start + 1: f_end], file_path=file_path)

    def split_f(self, str_eq, file_path, imgsize):
        index_f = 0
        brac_eq = self.get_brac_dict(str_eq)
        f_list = re.findall(r'\\f\(', str_eq)
        new_str_sub_list = []
        for _ in f_list:
            imgsize[1] = imgsize[1] + 1
            imgsize[0] = imgsize[0] + 1
            index_f = str_eq.index(r'\f(', index_f) + 1
            f_start = 0
            f_end = 0
            for brac in brac_eq:
                if int(brac) > int(index_f):
                    f_start = int(brac)
                    f_end = int(brac_eq.get(brac) or -1)
                    break
            f_str = self.deal_f(str_eq[f_start + 1: f_end], file_path, imgsize)
            new_str_sub_list.append({'fstr': f_str, 'fstart': f_start, 'fend': f_end})
        new_str = ""
        # f_start = 0
        f_end = 0
        str_eq = str_eq.replace(r'\f(', '   ')
        for new_sub in new_str_sub_list:
            new_str = new_str + str_eq[f_end: new_sub.get('fstart')] + new_sub.get('fstr')
            # f_start = new_sub.get('fstart')
            f_end = new_sub.get('fend') + 1
        if f_end < len(str_eq):
            new_str = new_str + str_eq[f_end:]
        return new_str.replace(' ', '')

    def split_r(self, str_eq, file_path, imgsize):
        index_r = 0
        brac_eq = self.get_brac_dict(str_eq)
        r_list = re.findall(r'\\r', str_eq)
        new_str_sub_list = []
        for _ in r_list:
            imgsize[1] = imgsize[1] + 0.5
            imgsize[0] = imgsize[0] + 1
            index_r = str_eq.index(r'\r', index_r) + 1
            f_start = 0
            f_end = 0
            for brac in brac_eq:
                if int(brac) > int(index_r):
                    f_start = int(brac)
                    f_end = int(brac_eq.get(brac))
                    break
            f_str = self.deal_r(str_eq[f_start + 1: f_end], file_path, imgsize)
            new_str_sub_list.append({'fstr': f_str, 'fstart': f_start, 'fend': f_end})
        new_str = ""
        # f_start = 0
        f_end = 0
        str_eq = str_eq.replace(r'\r', '  ')
        for new_sub in new_str_sub_list:
            new_str = new_str + str_eq[f_end: new_sub.get('fstart')] + new_sub.get('fstr')
            # f_start = new_sub.get('fstart')
            f_end = new_sub.get('fend') + 1
        if f_end < len(str_eq):
            new_str = new_str + str_eq[f_end:]
        return new_str.replace(' ', '')

    def split_b(self, str_eq, file_path, imgsize):
        index_r = 0
        brac_eq = self.get_brac_dict(str_eq)
        r_list = re.findall(r'\\b', str_eq)
        new_str_sub_list = []
        new_str_tmp = str_eq
        for _ in r_list:
            imgsize[0] = imgsize[0] + 2
            index_r = str_eq.index(r'\b', index_r) + 1
            f_start = 0
            f_end = 0
            left_ch = '('
            right_ch = '.'
            if 'lc' in str_eq:
                index_left = str_eq.index(r'lc')
                if index_r < index_left:
                    left_ch = str_eq[index_left + 3]
                    index_r = index_left + 4
                    new_str_tmp = new_str_tmp[:index_left - 1] + ' ' * 5 + new_str_tmp[index_left + 4:]
            if 'rc' in str_eq:
                index_right = str_eq.index('rc')
                if index_r < index_right:
                    right_ch = str_eq[index_right + 3]
                    index_r = index_right + 4
                    new_str_tmp = new_str_tmp[:index_right - 1] + ' ' * 5 + new_str_tmp[index_right + 4:]
            for brac in brac_eq:
                if int(brac) >= int(index_r):
                    f_start = int(brac)
                    f_end = int(brac_eq.get(brac))
                    break
            f_str = self.deal_b(str_eq[f_start + 1: f_end], file_path=file_path, left_char=left_ch, right_char=right_ch,
                                imgsize=imgsize)
            new_str_sub_list.append({'fstr': f_str, 'fstart': f_start, 'fend': f_end})
        new_str = ""
        # f_start = 0
        f_end = 0
        str_eq = new_str_tmp.replace(r'\b', '  ')

        for new_sub in new_str_sub_list:
            new_str = new_str + str_eq[f_end: new_sub.get('fstart')] + new_sub.get('fstr')
            # f_start = new_sub.get('fstart')
            f_end = new_sub.get('fend') + 1
        if f_end < len(str_eq):
            new_str = new_str + str_eq[f_end:]
        return new_str.replace(' ', '')

    def deal_o(self, str_eq, file_path=''):
        r"""\o(=, \s\up7(点燃)) """
        img_base = Image.new('RGB', (1200, 1200), 'white')
        font_normal = imf.truetype(os.path.join(
            current_app.config['BASEDIR'], 'jinrui', 'PingFang Medium_downcc.otf'), 24)
        x, y = 0, 0
        dw = imd.Draw(img_base)
        new_str_list = str_eq.split(',')
        new_str_dict = {}
        for i, new_sub in enumerate(new_str_list):
            new_sub.replace(r'\s', '')
            if 'up' in new_sub:
                dev = re.findall(r'up\d', new_sub)[0]
                dev_value = new_sub.split(dev)[-1]
                eq_brac_dict = self.get_brac_dict(dev_value)
                if eq_brac_dict:
                    min_brac = min(eq_brac_dict.keys())
                    dev_value = dev_value[min_brac + 1: eq_brac_dict.get(min_brac)]
                new_str_dict[dev] = dev_value
            elif 'do' in new_sub:
                dev = re.findall(r'do\d', new_sub)[0]
                dev_value = new_sub.split(dev)[-1]
                eq_brac_dict = self.get_brac_dict(dev_value)
                if eq_brac_dict:
                    min_brac = min(eq_brac_dict.keys())
                    dev_value = dev_value[min_brac + 1: eq_brac_dict.get(min_brac)]
                new_str_dict[dev] = dev_value
            else:
                dev = 'normal{}'.format(i)
                dev_value = new_sub
                new_str_dict[dev] = dev_value

        aps = sorted(new_str_dict.keys(), reverse=True)
        max_x = x
        line_x = 0
        line_y = 0
        for k in aps:
            sub_value = new_str_dict.get(k)
            x_sub = 0

            if 'up' in k or 'do' in k:
                dw.text((x, y), sub_value, font=font_normal, fill='#000000')
                y += 36
                x_sub = 24 * len(sub_value) + x
            else:
                line_x = x
                line_y = y
                y += 16
                # x_sub = 24 * len(sub_value) + x
            if max_x < x_sub:
                max_x = x_sub
        dw.line((line_x, line_y, max_x, line_y), fill='#000000', width=2)
        dw.line((line_x, line_y + 8, max_x, line_y + 8), fill='#000000', width=2)
        x = max_x
        img_base.crop((0, 0, x, y)).save(file_path)
        self.upload_to_oss(file_path, msg='eq域')

    def deal_f(self, str_eq, file_path, imgsize):

        current_app.logger.info(str_eq)
        ep__list = str_eq.split(',')
        frac_str = r'\frac'
        frac_list = []
        for item in ep__list:
            current_app.logger.info(item)
            item = self.replace_item(item)
            item = self.replace_sign(item)
            if r'\r' in item:
                item = self.split_r(item, file_path, imgsize)
            if r'\b' in item:
                item = self.split_b(item, file_path, imgsize)
            frac_list.append('{{{0}}}'.format(item))
        frac_str = frac_str + "".join(frac_list)
        return frac_str

    def deal_b(self, str_eq, file_path, left_char='(', right_char='.', imgsize=[]):
        b_str = r''
        """进该方法之前需剔除掉\b  \a\vs4\al\co1(2x≥－9－x，,5x－1＞3（x＋1）.)"""

        new_str = str_eq.replace(r'\al', '').replace(r'\a', '').replace(r'\vs', '@').replace(r'\co', '@')
        if left_char == '{':
            left_char = r'\{'
        if right_char == '}':
            right_char = r'\}'
        new_str = re.sub(r'@\d', '', new_str)
        if re.findall(r"\\f", new_str):
            new_str = self.split_f(new_str, file_path, imgsize)
        if re.findall(r"\\r", new_str):
            new_str = self.split_r(new_str, file_path, imgsize)

        eq_brac_dict = self.get_brac_dict(new_str)
        if eq_brac_dict:
            min_brac = min(eq_brac_dict.keys())
            new_str = new_str[min_brac + 1: eq_brac_dict.get(min_brac)]
        # current_app.logger.info(new_str[1: -1])
        current_app.logger.info(new_str)
        new_list = new_str.split(',')
        if len(new_list) > 1:
            """多行方程组  无法直接使用latex 绘制 需要额外绘制大括号"""
            time_now = datetime.now()
            year = str(time_now.year)
            month = str(time_now.month)
            day = str(time_now.day)
            newPath = os.path.join(current_app.config['BASEDIR'], 'img', 'tmp', year, month, day)
            # tmp_name = 'tmp{}.png'

            # tmp_path = r'd:\tmp{}.png'
            font_size = {2: 128, 3: 228, 4: 300}
            name_list = []
            # formula2img(r'$\left\{\right.$', tmp_path.format('char'), img_size=(1, 5), font_size=128)
            # 准备部件配图
            for i, new_sub in enumerate(new_list):
                width = len(new_sub) / 6 * 4
                # formula2img(new_sub, tmp_path.format(i), img_size=(width, 1), font_size=64)
                tmp_name = self.random_name('.png')
                tmp_path = os.path.join(newPath, tmp_name)
                self.switch_draw(new_sub, img_size=[width, 1], file_path=tmp_path)
                img_tmp = Image.open(tmp_path)
                tmp_x, tmp_y = img_tmp.size
                name_list.append(tmp_path)
                img_tmp.crop((1, 1, tmp_x - 1, tmp_y - 1)).save(tmp_path)

            # 画基图
            img_base = Image.new('RGB', (1200, 1200), 'white')
            current_app.logger.info('get otf {}'.format(os.path.join(
                current_app.config['BASEDIR'], 'jinrui', 'PingFang Medium_downcc.otf')))

            font_normal = imf.truetype(os.path.join(
                current_app.config['BASEDIR'], 'jinrui', 'PingFang Medium_downcc.otf'), font_size.get(len(new_list)))
            current_app.logger.info('get otf over')
            dw = imd.Draw(img_base)
            x, y = 0, 0
            dw.text((x, y), '{', font=font_normal, fill='#000000')
            # img_char = Image.open(tmp_path.format('char'))
            # x, y = 0, 0
            # img_base.paste(img_char, (0, 0))
            # x = img_char.size[0]
            x = 64
            max_x = x
            for i in range(len(new_list)):
                tmp_path = name_list[i]
                img_tmp = Image.open(tmp_path)
                tmp_x, tmp_y = img_tmp.size
                # img_base.size
                img_base.paste(img_tmp, (x, y, x + tmp_x, y + tmp_y))
                y = tmp_y + y
                if max_x < x + tmp_x:
                    max_x = x + tmp_x
            # tmp_path = os.path.join(newPath, tmp_name.format('final'))
            img_base.crop((0, 0, max_x, y)).save(file_path)
            self.upload_to_oss(file_path, msg='eq域')
            return ''

        else:
            """单行括号"""
            new_str = self.replace_sign(new_str)
            new_str = self.replace_item(new_str)
            current_app.logger.info(new_str)

            b_str = r'\left{}{}\right{}'.format(left_char, new_str, right_char)
        return b_str

    def deal_r(self, str_eq, file_path, imgsize):
        r_str = r''
        current_app.logger.info(str_eq)
        new_str = str_eq
        if re.findall(r"\\f", new_str):
            new_str = self.split_f(new_str, file_path, imgsize)
        if re.findall(r"\\b", new_str):
            new_str = self.split_b(new_str, file_path, imgsize)
        new_str_list = new_str.split(',')
        if len(new_str_list) > 1:
            r_str = r'\sqrt[{}]{{{}}}'.format(new_str_list[0], new_str_list[-1])
        elif len(new_str_list) == 1:
            r_str = r'\sqrt{{{}}}'.format(new_str_list[0])
        else:
            r_str = new_str
        r_str = self.replace_sign(r_str)
        r_str = self.replace_item(r_str)
        return r_str

    def deal_s(self, str_eq):
        current_app.logger.info(str_eq)
        new_str = str_eq
        brac_eq = self.get_brac_dict(str_eq)
        index_s = new_str.index(r'\s')
        f_start = 0
        f_end = 0
        for brac in brac_eq:
            if int(brac) > int(index_s):
                f_start = int(brac)
                f_end = int(brac_eq.get(brac))
                break
        content = new_str[f_start + 1: f_end]
        if r'\up' in new_str:
            return "<sup>{}</sup>".format(content)
        elif r'\do' in new_str:
            return '<sub>{}</sub>'.format(content)

        # return r_str

    @staticmethod
    def formula2img(str_latex, out_file, img_size=(5, 3), font_size=16):
        fig = plt.figure(figsize=img_size)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.text(0.5, 0.5, str_latex, fontsize=font_size, verticalalignment='center', horizontalalignment='center')
        plt.savefig(out_file)
        # plt.show()
        # current_app.logger.info('OK')

    @staticmethod
    def replace_item(item):
        # 域标签修改
        if '<sup>' in item:
            item = item.replace('<sup>', '^').replace('</sup>', ' ')
            # item = item
        if '<sub>' in item:
            item = item.replace('<sub>', '_').replace('</sub>', ' ')
            # item

        return item

    @staticmethod
    def replace_sign(item):
        # if '≠' in item:
        #     item = item.replace('≠', r'\ne')
        # if '≥' in item:
        #     item = item.replace('≥', r'\ge')
        # if '≤' in item:
        #     item = item.replace('≤', r'\le')
        if '－' in item:
            item = item.replace('－', r'-')
        if '－' in item:
            item = item.replace('－', r'-')
        if '＞' in item:
            item = item.replace('＞', r'>')
        if '＜' in item:
            item = item.replace('＜', r'<')
        if '，' in item:
            item = item.replace('，', r',')
        if '＋' in item:
            item = item.replace('＋', r'+')
        if '（' in item:
            item = item.replace('（', r'(')
        if '）' in item:
            item = item.replace('）', r')')
        return item

    @staticmethod
    def get_brac_dict(str_eq):
        # 括号占位栈
        brac_dict = {}
        arrs = []
        for i, v in enumerate(str_eq):
            if v == '(':
                arrs.append(i)
                brac_dict.setdefault(i, None)
            elif v == ')':
                if arrs:
                    brac_dict[arrs[-1]] = i
                    arrs.pop()
        current_app.logger.info(brac_dict)
        return brac_dict


    def upload_to_oss(self, file_data, rename=False, msg=''):
        # todo 先测试 再上传oss
        # return

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
    def whichin(text):
        if "</w:t>" in text:
            if "</w:instrText" in text:
                if "</w:drawing>" in text:
                    return ["<w:t", "</w:t>", "<w:instrText", "</w:instrText>", "<a:blip", ">"]
                else:
                    return ["<w:t", "</w:t>", "<w:instrText", "</w:instrText>"]
            elif "</w:drawing>" in text:
                return ["<w:t", "</w:t>", "<a:blip", ">"]
            else:
                return ["<w:t", "</w:t>"]
        elif "</w:instrText" in text:
            if "</w:drawing>" in text:
                return ["<w:instrText", "</w:instrText>", "<a:blip", ">"]
            else:
                return ["<w:instrText", "</w:instrText>"]
        elif "</w:drawing>" in text:
            return ["<a:blip", ">"]
        else:
            return []

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
        del_list = os.listdir(filepath)
        for f in del_list:
            file_path = os.path.join(filepath, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
#
# from jinrui import create_app
# app = create_app()
# with app.app_context():
#     doc_path = r'C:\Users\shuai\Desktop\test\3\数学  推演卷（三） C卷答案.docx'
#     # doc_path = r'D:\teamsystem\jinrui-test\img\doc\2020\10\30\LMbKgJKutaAb5pZtpACz.docx'
#     cp = CAutopic()
#     papger = cp.transfordoc(doc_path)
#     # print(papger)
#     for i in papger:
#         print('{}'.format(papger.get(i)))
# #     a = r'''<w:fldChar w:fldCharType="begin"/>eq \f(1 350－1 150,\f(2,3)×120)<w:fldChar w:fldCharType="end"/>'''
# #     cp.draw_pic(a, r'D:\teamsystem\jinrui-test\img\doc\2020\10\30\LMbKgJKutaAb5pZtpACz.png')
