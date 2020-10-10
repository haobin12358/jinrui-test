# -*- coding: utf-8 -*-
import re, shutil, os, requests, zipfile, json
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
    path = "C:\\Users\\Administrator\\Desktop\\金睿\\科学\\科学\\高分卷  （二）\\B卷  高分卷（二）.docx"
    path2 = "C:\\Users\\Administrator\\Desktop\\金睿\\科学\\科学\\高分卷  （二）\\testA.docx"
    path3 = "C:\\Users\\Administrator\\Desktop\\金睿\\科学\\科学\\高分卷  （二）\\testA.zip"
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
        "token": "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxMzAyNTkxMzMxNzcxNzQ4MzUyIiwiaWF0IjoxNjAyMjMwMjYyLCJleHAiOjE2MDIzMTY2NjJ9.qtLClF7RyAEjDEBSKZTOAA9rXPffKeW1iH_s5Urldz1z2Cu1lTyQ_Cpiyxg7kBSTIpfsp5WZjo_H8DKtIm47bA"
    }
    url = "https://api.jinrui.sanbinit.cn/file/upload"
    doc = Document(path)
    doc_xml = doc._body._element.xml
    doc_rels = doc.part._rels
    rId_list = list(doc_rels)
    print(rId_list)
    target_list = []
    for rel in doc_rels:
        rel = doc_rels[rel]
        target_list.append(rel.target_ref)
        if "image" in rel.target_ref:
            img_name = re.findall("/(.*)", rel.target_ref)[0]
    body_xml = etree.fromstring(doc_xml)  # 转换成lxml结点
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
                if rId in use_str:
                    target_list_dict = target_list[rId_list.index(rId)].split("/")
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
                        use_str = use_str.replace("""<a:blip r:embed="{0}">""".format(rId), "<img>{0}</img>".format(url_response))
                    else:
                        use_str = use_str.replace("""<a:blip r:embed="{0}">""".format(rId),
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

test_json = {
    '1': '<div>1．下列实数中最小的数是()</div><div>A．2B．－3</div><div>C．0 D．－π</div>',
    '2': '<div>2．下列计算正确的是()</div><div>A．a<sup>2</sup>·a<sup>3</sup>＝a<sup>6</sup></div><div>B．(－a<sup>2</sup>)<sup>3</sup>＝a<sup>6</sup></div><div>C．a<sup>10</sup>÷a<sup>9</sup>＝a(a≠0)</div><div>D．(－c)<sup>2</sup>＝－c<sup>2</sup></div>',
    '3': '<div>3．如图1，直线a，b被直线c所截，与∠1是同位角的角是()</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image1.png</img></div><div>A．∠2</div><div>B．∠3</div><div>C．∠4</div><div>D．∠5</div>',
    '4': '<div>4．若分式<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/第四题图.png</img>＝0，则x的值是()</div><div>A．±2 B．2  C．－2 D．0</div>',
    '5': '<div>5．如图2是某个几何体的三视图，该几何体是()</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image2.png</img></div><div>A．圆锥</div><div>B．四棱锥</div><div>C．圆柱</div><div>D．四棱柱</div>',
    '6': '<div>6．四张分别画有平行四边形、菱形、等边三角形、圆的卡片，它们的背面都相同．现将它们背面朝上，从中任取一张，卡片上所画图形恰好是中心对称图形的概率是( )</div><div>A.<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/6A.png</img> B．1  C.<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/6C.png</img>  D.<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/6D.png</img></div>',
    '7': '<div>7．如图3，正方形ABCD的边长为4，点A的坐标为(－1，1)，AB平行于x轴，则点C的坐标为( )</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image3.png</img></div><div>A．(3，1)</div><div>B．(－1，1)</div><div>C．(3，5)</div><div>D．(－1，5)</div>',
    '8': '<div>8．如图4，为了测量河对岸l<sub>1</sub>上两棵古树A，B之间的距离，某数学兴趣小组在河这边沿着与AB平行的直线l<sub>2</sub>上取C，D两点，测得∠ACB＝15°，∠ACD＝45°，若l<sub>1</sub>，l<sub>2</sub>之间的距离为50 m，则A，B之间的距离为( )</div><div>A．50 m B．25 m</div><div>C.<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/8C.png</img>m D．(50－25<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/8D.png</img>)m</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image4.png</img></div>',
    '9': '<div>9．如图5，将△ABC绕点A按逆时针旋转50°后，得到△ADC′，则∠ABD的度数是()</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image5.png</img></div><div>A．30°</div><div>B．45°</div><div>C．65°</div><div>D．75°</div>',
    '10': '<div>10．图6①是甲、乙两个圆柱形水槽，一个圆柱形的空玻璃杯放置在乙槽中(空玻璃杯的厚度忽略不计)．将甲槽的水匀速注入乙槽的空玻璃杯中，甲水槽内最高水位y(cm)与注水时间t(min)之间的函数关系如图②线段DE所示，乙水槽(包括空玻璃杯)内最高水位y(cm)与注水时间t(min)之间的函数关系如图②折线O－A－B－C所示．记甲槽底面积为S<sub>1</sub>，乙槽底面积为S<sub>2</sub>，乙槽中玻璃杯底面积为S<sub>3</sub>，则S<sub>1</sub>∶S<sub>2</sub>∶S<sub>3</sub>的值为()</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image6.png</img></div><div>A．8∶5∶1 B．4∶5∶2</div><div>C．5∶8∶3 D．8∶10∶5</div><div></div>',
    '11': '<div>11．计算：(1)(x－2)(－x－2)＝__    __；</div><div>(2)(x－2y)<sup>2</sup>＝_     __．</div>',
    '12': '<div>12．如图7，∠1＝∠2，要使△ABE≌△ACE，还需添加一个条件是__        </div><div>_．(填上你认为适当的一个条件即可)</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image7.png</img></div>',
    '13': '<div>13．如图8是23名射击运动员的一次测试成绩的频数分布折线图，则射击成绩的中位数是__   __．</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image8.png</img></div><div>图8</div>',
    '14': '<div>14．定义运算a⊗b＝a(1－b)，下列给出了关于这种运算的几个结论：</div><div>①2⊗(－2)＝6；②a⊗b＝b⊗a；</div><div>③若a＋b＝0，则(a⊗a)＋(b⊗b)＝2ab；</div><div>④若a⊗b＝0，则a＝0.</div><div>其中正确结论的序号是_     __．(在横线上填上所有你认为正确结论的序号)</div>',
    '15': '<div>15．已知A地在B地正南方3 km处，甲、乙两人同时分别从A，B两地向正北方向匀速直行，他们与A地的距离s(km)与所行的时间t(h)之间的函数关系图象用如图9所示的AC和BD表示，当他们行走3 h后，他们之间的距离为____km.</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image9.png</img></div>',
    '16': '<div>16．一位小朋友在粗糙不打滑的“Z”字形平面轨道上滚动一个半径为10 cm的圆盘，如图10所示，AB与CD是水平的，BC与水平面的夹角为60°，其中AB＝60 cm，CD＝40 cm，BC＝40 cm，那么该小朋友将圆盘从A点滚动到D点其圆心所经过的路线长为_____cm.</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image10.png</img></div><div></div>',
    '17': '<div>17．(6分)计算：2<sup>－</sup><sup>1</sup>－<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/17题图.png</img>＋4cos30°＋(－1)<sup>2 020</sup>.</div><div>  </div><div></div>',
    '18': '<div>18．(6分)解不等式组<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/18题图.png</img></div><div></div><div></div><div></div>',
    '19': '<div>19．(6分)课前预习是学习的重要环节，为了了解所教班级学生完成课前预习的具体情况，某班主任对本班部分学生进行了为期半个月的跟踪调查，他将调查结果分为四类：A.优秀，B.良好，C.一般，D.较差，并将调查结果绘制成图11中两幅不完整的统计图．</div><div>(1)本次调查的样本容量是__  __，其中A类女生有__ __名，D类学生有__ _名；</div><div>(2)将条形统计图和扇形统计图补充完整；</div><div>(3)若从被调查的A类和D类学生中各随机选取一位学生进行“一帮一”辅导学习，即A类学生辅导D类学生，请用列表法或画树状图的方法求出所选两位同学中恰好是一位女同学辅导一位男同学的概率．</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image11.png</img></div><div>图11</div><div></div><div></div><div></div><div></div><div></div>',
    '20': '<div>20．(8分)“十字街”形象地说明了相互垂直的两条道路，清代数学家梅文鼎(1633～1721)最先以“十字”描绘相互垂直的两条直线．而“十字四边形”指的是对角线互相垂直的四边形(如图12①)，请在所给的单位边长为1的网格中按要求画出“十字四边形”，且该“十字四边形”的各个顶点落在格点上．</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image12.png</img></div><div>图12</div><div>(1)在图②中，画一个“十字四边形”，使其周长为4<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/20题图.png</img>；</div><div>(2)在图③中，画一个“十字四边形”，使其面积为6且有一个内角是直角．</div><div></div><div></div><div></div><div></div><div></div>',
    '21': '<div>21．(8分)如图13，OA，OB是⊙O的两条半径，OA⊥OB，C是半径OB上的一动点，连结AC并延长交⊙O于D，过点D作直线交OB延长线于E，且DE＝CE，已知OA＝8.</div><div>(1)求证：DE是⊙O的切线；</div><div>(2)当∠A＝30°时，求CD的长．</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image13.png</img></div><div></div><div></div><div></div><div></div><div></div><div></div>',
    '22': '<div>22．(10分)如图14，在平面直角坐标系中，抛物线与x轴交于A(－2，0)，B(4，0)两点，与y轴交于点C，且OB＝OC.</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image14.png</img> </div><div>(1)求抛物线的表达式．</div><div>(2)已知点D(0，－1)，点P为线段BC上一动点，延长DP交抛物线于点H，连结BH.</div><div>①当四边形ODHB的面积为9时，求点H的坐标；</div><div>②设m＝<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/22题图.png</img>，求m的最大值．</div><div></div><div></div><div></div>',
    '23': '<div>23．(10分)[探究]如图15①，直线l与坐标轴的正半轴分别交于A，B两点，与反比例函数y＝<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/23题题干.png</img>(k＞0，x＞0)的图象交于C，D两点(点C在点D的左边)，过点C作CE⊥y轴于点E，过点D作DF⊥x轴于点F，CE与DF交于点G(a，b)．</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image15.png</img></div><div>图15</div><div>(1)若<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/23-1.png</img>＝<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/23-2.png</img>，请用含n的代数式表示<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/23-3.png</img>；</div><div>(2)求证：AC＝BD.</div><div>[应用]如图②，直线l与坐标轴的正半轴分别交于A，B两点，与反比例函数y＝<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/23-4.png</img>(k＞0，x＞0)的图象交于C，D两点(点C在点D的左边)，已知<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/23-5.png</img>＝<img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/23-6.png</img>，△OBD的面积为1，试用含m的代数式表示k.</div><div></div><div></div><div></div><div></div>',
    '24': '<div>24．(12分)如图16①，在正方形ABCD中，E为AB的中点，FE⊥AB，交CD于点F，点P在直线EF上移动，连结PC，PA，回答下列问题：</div><div>(1)如图②，当点P在E的左侧，且∠PAE＝60°时，连结BD，交直线PC于点M，求∠DMC的度数；(请完成下列求解过程)</div><div>解：连结PB.</div><div>∵FE⊥AB，E为AB的中点，</div><div>∴PA＝PB，∵∠PAE＝60°，</div><div>∴△APB是__  __三角形，∠PBA＝60°，</div><div>∵四边形ABCD是正方形，</div><div>∴PB＝BC＝AB，且∠DAB＝∠ABC＝90°，∠DBC＝____°，</div><div>∴∠PBC＝150°，∴∠PCB＝__   __°，</div><div>∴∠DMC＝∠PCB＋∠DBC＝__    __°.</div><div>(2)如图③，在(1)的条件下，点P关于AB的对称点为点P′，连结CP′并延长交BD于点M′.求证：△MCM′是等边三角形；</div><div>(3)直线BD与直线EF、直线PC分别相交于点O和点M，若正方形的边长为2，是否存在点P，使△PMO的面积为1？若存在，求出OP的长度；若不存在，请说明理由．</div><div><img>https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/image16.png</img></div><div>图16</div><div></div><div></div>'
}

