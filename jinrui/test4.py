import pypandoc

# output = pypandoc.convert_file('1.html', 'md', outputfile="file1.md")
# output = pypandoc.convert_file('1.html', 'docx', outputfile="file2.docx")
# output = pypandoc.convert_file('file1.md', 'ppt', outputfile="file1.ppt")

use_html = """
<p style="margin-bottom: 0in; line-height: 150%"><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">1</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">．估计<img align="bottom" border="0" height="32" hspace="1" name="图片 407" src="https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/img/tmp/2020/11/24/3zIBlDZbMuz1qBXMzVfl_html_88ac29123f0b017c.png" width="39"/>
－</font></span></font><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">2</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">的值在</font></span></font><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">(</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">　　</font></span></font><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">)</font></font></font></p><p style="margin-bottom: 0in; line-height: 150%"><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">A</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">．</font></span></font><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">0</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">到</font></span></font><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">1</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">之间
</font></span></font><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">	B</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">．</font></span></font><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">1</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">到</font></span></font><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">2</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">之间</font></span></font></p><p style="margin-bottom: 0in; line-height: 150%"><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">C</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">．</font></span></font><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">2</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">到</font></span></font><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">3</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">之间
</font></span></font><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">	D</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">．</font></span></font><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">3</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">到</font></span></font><font face="宋体, serif"><font face="Times New Roman, serif"><font size="3" style="font-size: 12pt">4</font></font></font><font face="宋体"><span lang="zh-CN"><font size="3" style="font-size: 12pt">之间</font></span></font></p>
"""

import re
img_list = re.findall(r"<img.*?/>", use_html)
i = 0
img_src_list = []
for img in img_list:
    use_html = use_html.replace(img, "{0" + "[0]".format(i) + "}")
    img_url = re.findall(r'.+?src="(\S+)"', img)[0]
    img_src_list.append("<img src='{0}'></img>".format(img_url))
    i += 1
print(img_src_list)
text = re.sub(r"</?(.+?)>", "", use_html)
print(text)
text = text.format(img_src_list)
print(text)