import os, cv2
import fitz

pdf_dir = []

path = "C:\\Users\\Administrator\\Desktop\\jinrui\\testsheet"
sheet_json = [{"dot":[46,356],"every_height":15.118110236220472,"every_width":120.94488188976378,"height":111.496062992126,"name":"一、选择题","num":10,"padding":5.67,"page":1,"score":3,"score_dot":[688.38,271.95],"score_height":4,"score_width":9,"show_title":1,"start":1,"title_height":15.58,"type":"select","width":681,"total_score":30,"index":0},{"dot":[46,467.496062992126],"every_height":30.236220472440944,"every_width":681,"height":51.0236220472441,"name":"二、填空题","num":1,"padding":0,"page":1,"score":4,"score_dot":[645.6299212598425,490.84251968503935],"score_height":25.118110236220474,"score_width":84.37007874015748,"show_title":1,"start":11,"title_height":15.58,"type":"fill","width":681,"every_score":[4,3,0],"total_score":4,"index":1},{"dot":[46,518.5196850393701],"every_height":30.236220472440944,"every_width":681,"height":32.125984251968504,"name":"二、填空题","num":1,"padding":0,"page":1,"score":4,"score_dot":[645.6299212598425,522.9685039370079],"score_height":25.118110236220474,"score_width":84.37007874015748,"show_title":0,"start":12,"title_height":15.58,"type":"fill","width":681,"every_score":[4,2,0],"total_score":4,"index":2},{"dot":[46,550.6456692913385],"every_height":30.236220472440944,"every_width":681,"height":32.125984251968504,"name":"二、填空题","num":1,"padding":0,"page":1,"score":4,"score_dot":[672.0866141732283,555.0944881889764],"score_height":25.118110236220474,"score_width":57.91338582677166,"show_title":0,"start":13,"title_height":15.58,"type":"fill","width":681,"every_score":[4,0],"total_score":4,"index":3},{"dot":[46,582.771653543307],"every_height":30.236220472440944,"every_width":681,"height":32.125984251968504,"name":"二、填空题","num":1,"padding":0,"page":1,"score":4,"score_dot":[672.0866141732283,587.2204724409448],"score_height":25.118110236220474,"score_width":57.91338582677166,"show_title":0,"start":14,"title_height":15.58,"type":"fill","width":681,"every_score":[4,0],"total_score":4,"index":4},{"dot":[46,614.8976377952755],"every_height":30.236220472440944,"every_width":681,"height":32.125984251968504,"name":"二、填空题","num":1,"padding":0,"page":1,"score":4,"score_dot":[672.0866141732283,619.3464566929133],"score_height":25.118110236220474,"score_width":57.91338582677166,"show_title":0,"start":15,"title_height":15.58,"type":"fill","width":681,"every_score":[4,0],"total_score":4,"index":5},{"dot":[46,647.023622047244],"every_height":30.236220472440944,"every_width":681,"height":32.125984251968504,"name":"二、填空题","num":1,"padding":0,"page":1,"score":4,"score_dot":[672.0866141732283,651.4724409448818],"score_height":25.118110236220474,"score_width":57.91338582677166,"show_title":0,"start":16,"title_height":15.58,"type":"fill","width":681,"every_score":[4,0],"total_score":4,"index":6},{"dot":[46,679.1496062992125],"every_height":48,"every_width":681,"height":229.44094488188978,"name":"三、解答题","num":1,"padding":0,"page":1,"score":6,"score_dot":[539.8031496062993,702.4960629921259],"score_height":25.118110236220474,"score_width":190.1968503937008,"show_title":1,"start":17,"title_height":15.58,"type":"answer","width":681,"every_score":[6,5,4,3,2,1,0],"total_score":6,"index":7},{"dot":[46,75.59055118110237],"every_height":48,"every_width":681,"height":229.44094488188978,"name":"四、解答题","num":1,"padding":0,"page":2,"score":6,"score_dot":[539.8031496062993,98.93700787401576],"score_height":25.118110236220474,"score_width":190.1968503937008,"show_title":1,"start":18,"title_height":15.58,"type":"answer","width":681,"every_score":[6,5,4,3,2,1,0],"total_score":6,"index":8},{"dot":[46,305.0314960629921],"every_height":48,"every_width":681,"height":229.44094488188978,"name":"五、解答题","num":1,"padding":0,"page":2,"score":6,"score_dot":[539.8031496062993,328.3779527559055],"score_height":25.118110236220474,"score_width":190.1968503937008,"show_title":1,"start":19,"title_height":15.58,"type":"answer","width":681,"every_score":[6,5,4,3,2,1,0],"total_score":6,"index":9},{"dot":[46,534.4724409448819],"every_height":48,"every_width":681,"height":229.44094488188978,"name":"六、解答题","num":1,"padding":0,"page":2,"score":8,"score_dot":[486.8897637795276,557.8188976377953],"score_height":25.118110236220474,"score_width":243.11023622047244,"show_title":1,"start":20,"title_height":15.58,"type":"answer","width":681,"every_score":[8,7,6,5,4,3,2,1,0],"total_score":8,"index":10},{"dot":[46,763.9133858267717],"every_height":48,"every_width":681,"height":229.44094488188978,"name":"七、解答题","num":1,"padding":0,"page":2,"score":8,"score_dot":[486.8897637795276,787.2598425196851],"score_height":25.118110236220474,"score_width":243.11023622047244,"show_title":1,"start":21,"title_height":15.58,"type":"answer","width":681,"every_score":[8,7,6,5,4,3,2,1,0],"total_score":8,"index":11},{"dot":[46,75.59055118110237],"every_height":48,"every_width":681,"height":229.44094488188978,"name":"八、解答题","num":1,"padding":0,"page":3,"score":10,"score_dot":[407.5196850393701,98.93700787401576],"score_height":25.118110236220474,"score_width":322.4803149606299,"show_title":1,"start":22,"title_height":15.58,"type":"answer","width":681,"every_score":[1,"",9,8,7,6,5,4,3,2,1,0],"total_score":10,"index":12},{"dot":[46,305.0314960629921],"every_height":48,"every_width":681,"height":229.44094488188978,"name":"九、解答题","num":1,"padding":0,"page":3,"score":10,"score_dot":[407.5196850393701,328.3779527559055],"score_height":25.118110236220474,"score_width":322.4803149606299,"show_title":1,"start":23,"title_height":15.58,"type":"answer","width":681,"every_score":[1,"",9,8,7,6,5,4,3,2,1,0],"total_score":10,"index":13},{"dot":[46,534.4724409448819],"every_height":48,"every_width":681,"height":229.44094488188978,"name":"十、解答题","num":1,"padding":0,"page":3,"score":12,"score_dot":[407.5196850393701,557.8188976377953],"score_height":25.118110236220474,"score_width":322.4803149606299,"show_title":1,"start":24,"title_height":15.58,"type":"answer","width":681,"every_score":["1","",9,8,7,6,5,4,3,2,1,0],"total_score":12,"index":14}]

def get_file():
    docunames = os.listdir(path)
    for docuname in docunames:
        if os.path.splitext(docuname)[1] == '.pdf':  # 目录下包含.pdf的文件
            pdf_dir.append(docuname)

name_dir = []
def get_name():
    for pdf in pdf_dir:
        if pdf.replace(".pdf", "") not in name_dir:
            name_dir.append(pdf.replace(".pdf", ""))

jpg_dir = []
def get_jpg():
    jpgs = os.listdir(path)
    for jpg in jpgs:
        if os.path.splitext(jpg)[1] == '.jpg':
            jpg_dir.append(jpg)

def conver_img():
    for pdf in pdf_dir:
        doc = fitz.Document(os.path.abspath(path) + "\\" + pdf)
        pdf_name = os.path.splitext(pdf)[0]
        i = 1
        for pg in range(doc.pageCount):
            page = doc[pg]
            rotate = int(0)
            # 每个尺寸的缩放系数为2，这将为我们生成分辨率提高四倍的图像。
            zoom_x = 2.0
            zoom_y = 2.0
            trans = fitz.Matrix(zoom_x, zoom_y).preRotate(rotate)
            pm = page.getPixmap(matrix=trans, alpha=False)
            pm.writePNG(path + '\\{0}.jpg'.format(pdf_name + "-" +str(i)))
            i = i + 1

index_h = 1684 / 1124.52
index_w = 1191 / 810.81
width_less = 4
height_less = -30

# 存储图片
def label2picture(cropImg, framenum, tracker):
    """
    cropImg: 图片
    framenum: 文件名
    tracker: 存储文件夹
    """
    pathnew = path + "\\"
    # cv2.imshow("image", cropImg)
    # cv2.waitKey(1)
    if (os.path.exists(pathnew + tracker)):
        print(">>>>>>>>>>>>>>>>>" + framenum)
        cv2.imwrite(pathnew + tracker + '\\' + framenum + '.jpg', cropImg, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

    else:
        os.makedirs(pathnew + tracker)
        cv2.imwrite(pathnew + tracker + '\\' + framenum + '.jpg', cropImg, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
# 剪裁sn
def cut_sn():
    for jpg in jpg_dir:
        jpg_name_dict = jpg.replace(".jpg", "").split("-")
        if int(jpg_name_dict[1]) % 4 == 1:
            img = cv2.imread(r"{0}".format(path + "\\" + jpg))
            sn_w = 600 + width_less
            sn_y = 40 + height_less
            sn_height = 16
            sn_width = 115
            print(int(sn_y * index_h))
            print(int(sn_w * index_w))
            crop_img = img[int(sn_y * index_h): int((sn_y + sn_height) * index_h),
                           int(sn_w * index_w): int((sn_w + sn_width) * index_w)]
            label2picture(crop_img, "sn-{0}".format(str(int(int(jpg_name_dict[1]) / 4))), jpg_name_dict[0])

# 剪裁准考证区域
def cut_no():
    for jpg in jpg_dir:
        jpg_name_dict = jpg.replace(".jpg", "").split("-")
        if int(jpg_name_dict[1]) % 4 == 1:
            img = cv2.imread(r"{0}".format(path + "\\" + jpg))
            sn_w = 530 + width_less
            sn_y = 154 + height_less
            sn_height = 200
            sn_width = 235
            print(int(sn_y * index_h))
            print(int(sn_w * index_w))
            crop_img = img[int(sn_y * index_h): int((sn_y + sn_height) * index_h),
                       int(sn_w * index_w): int((sn_w + sn_width) * index_w)]
            label2picture(crop_img, "no-{0}".format(str(int(int(jpg_name_dict[1]) / 4))), jpg_name_dict[0])

# 剪裁单选
def cut_select():
    for sheet in sheet_json:
        if sheet["type"] == "select":
            page = sheet["page"]
            for name in name_dir:
                i = 0
                jpg_name = name + "-" + str(i + page) + ".jpg"
                while jpg_name in jpg_dir:
                    select_x = sheet["dot"][0]
                    select_y = sheet["dot"][1]
                    img = cv2.imread(path + "\\" + jpg_name)
                    j = 0
                    while j < sheet["num"]:
                        up = 26.37 + (j % 5) * sheet["every_height"] + height_less
                        left = (int(j / 5)) * sheet["every_width"] + width_less
                        print(int((select_y + up) * index_h))
                        print(int((select_x + left) * index_w))
                        crop_img = img[int((select_y + up) * index_h): int(
                          (select_y + sheet["every_height"] + up) * index_h),
                                   int((select_x + left) * index_w): int(
                                     (select_x + left + sheet["every_width"]) * index_w)]
                        label2picture(crop_img, "{0}-{1}-{2}-{3}".format(sheet["type"], str(int(i / 4)),
                                                                         str(sheet["index"] + 1), str(j + 1)),
                                      name)
                        j = j + 1

                    i = i + 4
                    jpg_name = name + "-" + str(i + page) + ".jpg"


# 剪裁多选
def cut_multi():
    for sheet in sheet_json:
        if sheet["type"] == "multi":
            page = sheet["page"]
            for name in name_dir:
                i = 0
                jpg_name = name + "-" + str(i + page) + ".jpg"
                while jpg_name in jpg_dir:
                    select_x = sheet["dot"][0]
                    select_y = sheet["dot"][1]
                    img = cv2.imread(path + "\\" + jpg_name)
                    j = 0
                    while j < sheet["num"]:
                        up = 26.37 + (j % 5) * sheet["every_height"] + height_less
                        left = (int(j / 5)) * sheet["every_width"] + width_less
                        print(int((select_y + up) * index_h))
                        print(int((select_x + left) * index_w))
                        crop_img = img[int((select_y + up) * index_h): int(
                            (select_y + sheet["every_height"] + up) * index_h),
                                   int((select_x + left) * index_w): int(
                                       (select_x + left + sheet["every_width"]) * index_w)]
                        label2picture(crop_img, "{0}-{1}-{2}-{3}".format(sheet["type"], str(int(i / 4)),
                                                                         str(sheet["index"] + 1), str(j + 1)),
                                      name)
                        j = j + 1

                    i = i + 4
                    jpg_name = name + "-" + str(i + page) + ".jpg"

# 剪裁判断
def cut_judge():
    for sheet in sheet_json:
        if sheet["type"] == "judge":
            page = sheet["page"]
            for name in name_dir:
                i = 0
                jpg_name = name + "-" + str(i + page) + ".jpg"
                while jpg_name in jpg_dir:
                    select_x = sheet["dot"][0]
                    select_y = sheet["dot"][1]
                    img = cv2.imread(path + "\\" + jpg_name)
                    j = 0
                    while j < sheet["num"]:
                        up = 26.37 + (j % 5) * sheet["every_height"] + height_less
                        left = (int(j / 5)) * sheet["every_width"] + width_less
                        print(int((select_y + up) * index_h))
                        print(int((select_x + left) * index_w))
                        crop_img = img[int((select_y + up) * index_h): int(
                            (select_y + sheet["every_height"] + up) * index_h),
                                   int((select_x + left) * index_w): int(
                                       (select_x + left + sheet["every_width"]) * index_w)]
                        label2picture(crop_img, "{0}-{1}-{2}-{3}".format(sheet["type"], str(int(i / 4)),
                                                                         str(sheet["index"] + 1), str(j + 1)),
                                      name)
                        j = j + 1

                    i = i + 4
                    jpg_name = name + "-" + str(i + page) + ".jpg"

# 剪裁全量填空
def cut_fill_all():
    for sheet in sheet_json:
        if sheet["type"] == "fill":
            page = sheet["page"]
            for name in name_dir:
                i = 0
                jpg_name = name + "-" + str(i + page) + ".jpg"
                while jpg_name in jpg_dir:
                    select_x = sheet["dot"][0] + width_less
                    select_y = sheet["dot"][1] + height_less
                    img = cv2.imread(path + "\\" + jpg_name)
                    crop_img = img[int(select_y * index_h): int(
                        (select_y + sheet["height"]) * index_h),
                               int(select_x * index_w): int(
                                   (select_x + sheet["width"]) * index_w)]
                    label2picture(crop_img, "{0}-{1}-{2}-{3}".format(sheet["type"] + "all", str(int(i / 4)),
                                                                     str(sheet["index"] + 1), str(1)), name)

                    i = i + 4
                    jpg_name = name + "-" + str(i + page) + ".jpg"

# 剪裁ocr填空
def cut_fill_ocr():
    for sheet in sheet_json:
        if sheet["type"] == "fill":
            page = sheet["page"]
            for name in name_dir:
                i = 0
                jpg_name = name + "-" + str(i + page) + ".jpg"
                while jpg_name in jpg_dir:
                    select_x = sheet["score_dot"][0] + width_less
                    select_y = sheet["score_dot"][1] + height_less
                    img = cv2.imread(path + "\\" + jpg_name)
                    crop_img = img[int(select_y * index_h): int(
                        (select_y + sheet["score_height"]) * index_h),
                               int(select_x * index_w): int(
                                   (select_x + sheet["score_width"]) * index_w)]
                    label2picture(crop_img, "{0}-{1}-{2}-{3}".format(sheet["type"] + "ocr", str(int(i / 4)),
                                                                     str(sheet["index"] + 1), str(1)), name)

                    i = i + 4
                    jpg_name = name + "-" + str(i + page) + ".jpg"

# 剪裁全量简答
def cut_answer_all():
    for sheet in sheet_json:
        if sheet["type"] == "answer":
            page = sheet["page"]
            for name in name_dir:
                i = 0
                jpg_name = name + "-" + str(i + page) + ".jpg"
                while jpg_name in jpg_dir:
                    select_x = sheet["dot"][0] + width_less
                    select_y = sheet["dot"][1] + height_less
                    img = cv2.imread(path + "\\" + jpg_name)
                    crop_img = img[int(select_y * index_h): int(
                        (select_y + sheet["height"]) * index_h),
                               int(select_x * index_w): int(
                                   (select_x + sheet["width"]) * index_w)]
                    label2picture(crop_img, "{0}-{1}-{2}-{3}".format(sheet["type"] + "all", str(int(i / 4)),
                                                                     str(sheet["index"] + 1), str(1)), name)

                    i = i + 4
                    jpg_name = name + "-" + str(i + page) + ".jpg"

# 剪裁ocr简答
def cut_answer_ocr():
    for sheet in sheet_json:
        if sheet["type"] == "answer":
            page = sheet["page"]
            for name in name_dir:
                i = 0
                jpg_name = name + "-" + str(i + page) + ".jpg"
                while jpg_name in jpg_dir:
                    select_x = sheet["score_dot"][0] + width_less
                    select_y = sheet["score_dot"][1] + height_less
                    img = cv2.imread(path + "\\" + jpg_name)
                    crop_img = img[int(select_y * index_h): int(
                        (select_y + sheet["score_height"]) * index_h),
                               int(select_x * index_w): int(
                                   (select_x + sheet["score_width"]) * index_w)]
                    label2picture(crop_img, "{0}-{1}-{2}-{3}".format(sheet["type"] + "ocr", str(int(i / 4)),
                                                                     str(sheet["index"] + 1), str(1)), name)

                    i = i + 4
                    jpg_name = name + "-" + str(i + page) + ".jpg"


if __name__ == '__main__':
    get_file()
    print(">>>>>>>>>>>>>>>>>pdf_dir:" + str(pdf_dir))
    get_name()
    conver_img()
    get_jpg()
    print(">>>>>>>>>>>>>>>>>jpg_dir:" + str(jpg_dir))
    cut_sn()
    cut_no()
    cut_select()
    cut_judge()
    cut_multi()
    cut_fill_all()
    cut_answer_all()
    cut_fill_ocr()
    cut_answer_ocr()