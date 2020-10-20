# -*- coding: utf-8 -*-
import re, shutil, os, requests, zipfile, json, oss2, uuid
from docx import Document
from lxml import etree

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

if __name__ == "__main__":
    path = "C:\\Users\\Administrator\\Desktop\\jinrui\\math\\数学  推演卷（一） C卷答案.docx"
    path2 = "C:\\Users\\Administrator\\Desktop\\jinrui\\math\\testCA.docx"
    path3 = "C:\\Users\\Administrator\\Desktop\\jinrui\\math\\testCA.zip"
    shutil.copyfile(path, path2)
    os.rename(path2, path3)
    zip_file = zipfile.ZipFile(path3)
    if os.path.isdir(path3 + "_files"):
        pass
    else:
        os.mkdir(path3 + "_files")
    for names in zip_file.namelist():
        zip_file.extract(names, path3 + "_files/")
    zip_file.close()

    header = {
        "token": "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxMzAyNTkxMzMxNzcxNzQ4MzUyIiwiaWF0IjoxNjAyNTY1NDUwLCJleHAiOjE2MDI2NTE4NTB9.HO0k0uePIIXd0-pxh2nJAK8NJvNNmQdqsMz_3ZprAzg_uk6nb3hCX-w_RlmXpIzV_o-uDRovIRe5_DbFgQdp3A"
    }
    url = "https://api.jinrui.sanbinit.cn/file/upload"
    doc = Document(path)
    doc_xml = doc._body._element.xml
    doc_rels = doc.part._rels
    rId_list = list(doc_rels)
    print(rId_list)
    print(len(rId_list))
    target_list = []

    for rel in doc_rels:
        rel = doc_rels[rel]
        target_list.append(rel.target_ref)
        if "image" in rel.target_ref:
            img_name = re.findall("/(.*)", rel.target_ref)[0]
    body_xml = etree.fromstring(doc_xml)  # 转换成lxml结点
    print(target_list)
    print(len(target_list))
    i = 0
    paper_num = 0
    paper_dict = {}
    while i < len(body_xml):
        # print("第{0}行".format(str(i + 1)))
        if i == 2222:
            print(str(etree.tounicode(body_xml[i])))
        in_text = whichin(str(etree.tounicode(body_xml[i])))
        if "</w:instrText>" in in_text or "</w:t>":
            in_text.append("<w:vertAlign")
            in_text.append("/>")
        if not len(in_text) or len(in_text) % 2 != 0:
            re_str = "<w:r>|</w:r>"
        else:
            re_str = "<w:r>|</w:r>"
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
        if re_str:
            use_list = re.findall(r"{0}".format(re_str), str(etree.tounicode(body_xml[i])))
        else:
            use_list = []
        use_str = ""
        index = 0
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
            use_str = use_str + use_list[index].replace("<w:t>", "").replace("</w:t>", "").replace("""<w:t xml:space="preserve">""", "")
            index = index + 1
        use_str = use_str.replace("<w:r>", "").replace("</w:r>", "").replace("\u3000", "")
        if "<a:blip" in use_str:
            for rId in rId_list:

                if """<a:blip r:embed="{0}"/>""".format(rId) in use_str:
                    target_list_dict = target_list[rId_list.index(rId)].split("/")
                    print(use_str)
                    print(">>>>>>>>>>>target_dict:" + str(target_list_dict))
                    if len(target_list_dict) > 1:
                        print(">>>>>>>>>>target_list_dict:" + str(target_list_dict))
                        picture_path = path3 + "_files\\word" + "\\" + target_list_dict[0] + "\\" + target_list_dict[1]
                        files = {
                            "file": (target_list_dict[1], open(r"{0}".format(picture_path), "rb"), "image/png")
                        }
                        response = requests.post(headers=header, files=files, url=url)
                        json_response = json.loads(response.content)
                        url_response = json_response["data"]["url"]
                        print(">>>>>>>>>>>>>>>>>>url_response:" + str(url_response))
                        use_str = use_str.replace("""<a:blip r:embed="{0}"/>""".format(rId),
                                                  "<img src='{0}'></img>".format(url_response))
                    else:
                        use_str = use_str.replace("""<a:blip r:embed="{0}"/>""".format(rId),
                                                  "<img src='{0}'></img>".format(str(target_list[rId_list.index(rId)])))
        use_str = use_str.replace("<w:instrText>", "").replace("</w:instrText>", "")\
            .replace("""<w:instrText xml:space="preserve">""", "")

        use_str = use_str\
            .replace("<w:tbl ", """<table border="1">""")\
            .replace("<w:tr>", "<tr>")\
            .replace("<w:tc>", "<td>")\
            .replace("</w:tc>", "</td>")\
            .replace("</w:tr>", "</tr>")\
            .replace("</w:tbl>", "</table>")
        print(use_str)
        point_use = "．"  # 用来区分题目的点位
        # point_use = "."
        if (str(paper_num + 1) + point_use) in use_str:
            paper_num = paper_num + 1
        point_icon = str(paper_num) + point_use
        pass_list = ["一、", "二、", "三、", "四、", "五、", "六、", "七、", "八、", "九、"]
        for row in pass_list:
            if row in use_str and point_icon not in use_str:
                use_str = ""
        if point_icon in use_str or str(paper_num) in paper_dict.keys():
            if str(paper_num) in paper_dict.keys():
                paper_dict[str(paper_num)] = paper_dict[str(paper_num)] + "<div>" + use_str + "</div>"
            else:
                paper_dict[str(paper_num)] = "<div>" + use_str + "</div>"
        i = i + 1
    print(paper_dict)

