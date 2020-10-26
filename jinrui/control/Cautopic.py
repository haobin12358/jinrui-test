import os
import re
from datetime import datetime

from PIL import Image
from PIL import ImageFont as imf
from PIL import ImageDraw as imd
import matplotlib.pyplot as plt
from flask import current_app

from jinrui.extensions.error_response import ParamsError
from jinrui.extensions.register_ext import ali_oss


class CAutopic():

    def get_eqcontent(self, str_eq):
        try:
            eqcontent = \
                re.findall(r'''<w:fldChar w:fldCharType="begin"/>eq (.*?)<w:fldChar w:fldCharType="end"/>''', str_eq)[0]
            current_app.logger.info(eqcontent)
            return eqcontent
        except:
            raise ParamsError('数据异常')

    def draw_pic(self, deaL_str, file_path, img_size=[]):
        if not img_size:
            img_size = [1, 1]
        eq_str = self.get_eqcontent(deaL_str)
        self.switch_draw(eq_str, img_size, file_path=file_path)

    def switch_draw(self, eq_str, img_size, file_path):

        if eq_str.startswith('\\b'):
            draw_str = self.split_b(eq_str, img_size)
            if draw_str:
                draw_str = '${}$'.format(draw_str)
        elif eq_str.startswith('\\f'):
            draw_str = self.split_f(eq_str, img_size)
            if draw_str:
                draw_str = '${}$'.format(draw_str)
        elif eq_str.startswith('\\r'):
            draw_str = self.split_r(eq_str, img_size)
            if draw_str:
                draw_str = '${}$'.format(draw_str)
        elif eq_str.startswith('\\o'):
            self.split_o(eq_str, file_path=file_path)
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
        # todo 上传oss
        time_now = datetime.now()
        year = str(time_now.year)
        month = str(time_now.month)
        day = str(time_now.day)
        img_name = str(file_path).split('/')[-1]
        data = '/img/{folder}/{year}/{month}/{day}/{img_name}'.format(folder='tmp', year=year,
                                                                      month=month, day=day,
                                                                      img_name=img_name)

        self.upload_to_oss(file_path, data[1:], 'eq域')
        return True

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

    def split_f(self, str_eq, imgsize):
        index_f = 0
        brac_eq = self.get_brac_dict(str_eq)
        f_list = re.findall(r'\\f', str_eq)
        new_str_sub_list = []
        for _ in f_list:
            imgsize[1] = imgsize[1] + 1
            imgsize[0] = imgsize[0] + 1
            index_f = str_eq.index(r'\f', index_f)
            f_start = 0
            f_end = 0
            for brac in brac_eq:
                if int(brac) > int(index_f):
                    f_start = int(brac)
                    f_end = int(brac_eq.get(brac))
                    break
            f_str = self.deal_f(str_eq[f_start + 1: f_end], imgsize)
            new_str_sub_list.append({'fstr': f_str, 'fstart': f_start, 'fend': f_end})
        new_str = ""
        # f_start = 0
        f_end = 0
        str_eq = str_eq.replace(r'\f', '  ')
        for new_sub in new_str_sub_list:
            new_str = new_str + str_eq[f_end: new_sub.get('fstart')] + new_sub.get('fstr')
            # f_start = new_sub.get('fstart')
            f_end = new_sub.get('fend') + 1
        if f_end < len(str_eq):
            new_str = new_str + str_eq[f_end:]
        return new_str.replace(' ', '')

    def split_r(self, str_eq, imgsize):
        index_r = 0
        brac_eq = self.get_brac_dict(str_eq)
        r_list = re.findall(r'\\r', str_eq)
        new_str_sub_list = []
        for _ in r_list:
            imgsize[1] = imgsize[1] + 0.5
            imgsize[0] = imgsize[0] + 0.5
            index_r = str_eq.index(r'\r', index_r)
            f_start = 0
            f_end = 0
            for brac in brac_eq:
                if int(brac) > int(index_r):
                    f_start = int(brac)
                    f_end = int(brac_eq.get(brac))
                    break
            f_str = self.deal_r(str_eq[f_start + 1: f_end], imgsize)
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

    def split_b(self, str_eq, imgsize):
        index_r = 0
        brac_eq = self.get_brac_dict(str_eq)
        r_list = re.findall(r'\\b', str_eq)
        new_str_sub_list = []
        new_str_tmp = str_eq
        for _ in r_list:
            imgsize[0] = imgsize[0] + 2
            index_r = str_eq.index(r'\b', index_r)
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
            f_str = self.deal_b(str_eq[f_start + 1: f_end], left_char=left_ch, right_char=right_ch, imgsize=imgsize)
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
        font_normal = imf.truetype(os.path.join('./', 'PingFang Medium_downcc.otf'), 24)
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

    def deal_f(self, str_eq, imgsize):
        # todo 提取$
        current_app.logger.info(str_eq)
        ep__list = str_eq.split(',')
        frac_str = r'\frac'
        frac_list = []
        for item in ep__list:
            current_app.logger.info(item)
            item = self.replace_item(item)
            item = self.replace_sign(item)
            if r'\r' in item:
                item = self.split_r(item, imgsize)
            if r'\b' in item:
                item = self.split_b(item, imgsize)
            frac_list.append('{{{0}}}'.format(item))
        frac_str = frac_str + "".join(frac_list)
        return frac_str

    def deal_b(self, str_eq, left_char='(', right_char='.', imgsize=[]):
        b_str = r''
        """进该方法之前需剔除掉\b  \a\vs4\al\co1(2x≥－9－x，,5x－1＞3（x＋1）.)"""

        new_str = str_eq.replace(r'\al', '').replace(r'\a', '').replace(r'\vs', '@').replace(r'\co', '@')
        if left_char == '{':
            left_char = r'\{'
        if right_char == '}':
            right_char = r'\}'
        new_str = re.sub(r'@\d', '', new_str)
        if re.findall(r"\\f", new_str):
            new_str = self.split_f(new_str, imgsize)
        if re.findall(r"\\r", new_str):
            new_str = self.split_r(new_str, imgsize)

        eq_brac_dict = self.get_brac_dict(new_str)
        if eq_brac_dict:
            min_brac = min(eq_brac_dict.keys())
            new_str = new_str[min_brac + 1: eq_brac_dict.get(min_brac)]
        # print(new_str[1: -1])
        current_app.logger.info(new_str)
        new_list = new_str.split(',')
        if len(new_list) > 1:
            """多行方程组  无法直接使用latex 绘制 需要额外绘制大括号"""
            tmp_path = r'd:\tmp{}.png'
            font_size = {2: 128, 3: 228, 4: 300}
            # formula2img(r'$\left\{\right.$', tmp_path.format('char'), img_size=(1, 5), font_size=128)
            # 准备部件配图
            for i, new_sub in enumerate(new_list):
                width = len(new_sub) / 6 * 4
                # formula2img(new_sub, tmp_path.format(i), img_size=(width, 1), font_size=64)
                self.switch_draw(new_sub, img_size=[width, 1], file_path=tmp_path.format(i))
                img_tmp = Image.open(tmp_path.format(i))
                tmp_x, tmp_y = img_tmp.size
                img_tmp.crop((1, 1, tmp_x - 1, tmp_y - 1)).save(tmp_path.format(i))

            # 画基图
            img_base = Image.new('RGB', (1200, 1200), 'white')
            font_normal = imf.truetype(os.path.join('./', 'PingFang Medium_downcc.otf'), font_size.get(len(new_list)))
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
                img_tmp = Image.open(tmp_path.format(i))
                tmp_x, tmp_y = img_tmp.size
                # img_base.size
                img_base.paste(img_tmp, (x, y, x + tmp_x, y + tmp_y))
                y = tmp_y + y
                if max_x < x + tmp_x:
                    max_x = x + tmp_x
            img_base.crop((0, 0, max_x, y)).save(tmp_path.format('final'))
            return ''

        else:
            """单行括号"""
            new_str = self.replace_sign(new_str)
            new_str = self.replace_item(new_str)
            current_app.logger.info(new_str)

            b_str = r'\left{}{}\right{}'.format(left_char, new_str, right_char)
        return b_str

    def deal_r(self, str_eq, imgsize):
        r_str = r''
        current_app.logger.info(str_eq)
        new_str = str_eq
        if re.findall(r"\\f", new_str):
            new_str = self.split_f(new_str, imgsize)
        if re.findall(r"\\b", new_str):
            new_str = self.split_b(new_str, imgsize)
        new_str_list = new_str.split(',')
        if len(new_str_list) > 1:
            r_str = r'\sqrt[{}]{{{}}}'.format(new_str_list[0], new_str_list[-1])
        elif len(new_str_list) == 1:
            r_str = r'\sqrt{{{}}}'.format(new_str_list[0])
        else:
            r_str = new_str
        return r_str

    def formula2img(self, str_latex, out_file, img_size=(5, 3), font_size=16):
        fig = plt.figure(figsize=img_size)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.text(0.5, 0.5, str_latex, fontsize=font_size, verticalalignment='center', horizontalalignment='center')
        plt.savefig(out_file)
        # plt.show()
        # print('OK')

    def replace_item(self, item):
        # 域标签修改
        if '<sup>' in item:
            item = item.replace('<sup>', '^').replace('</sup>', ' ')
            # item = item
        if '<sub>' in item:
            item = item.replace('<sub>', '_').replace('</sub>', ' ')
            # item

        return item

    def replace_sign(self, item):
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
        if '，' in item:
            item = item.replace('，', r',')
        if '＋' in item:
            item = item.replace('＋', r'+')
        if '（' in item:
            item = item.replace('（', r'(')
        if '）' in item:
            item = item.replace('）', r')')
        return item

    def get_brac_dict(self, str_eq):
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

    @staticmethod
    def upload_to_oss(file_data, file_name, msg=''):
        if current_app.config.get('IMG_TO_OSS'):
            try:
                ali_oss.save(data=file_data, filename=file_name)
            except Exception as e:
                current_app.logger.error(">>> {} 上传到OSS出错 : {}  <<<".format(msg, e))
                raise ParamsError('服务器繁忙，请稍后再试')
