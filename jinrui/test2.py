import os, cv2
import fitz

pdf_dir = []

path = "C:\\Users\\Administrator\\Desktop\\jinrui\\testsheet"
sheet_json = [
    {
        "type":"answer",
        "name":"3",
        "num":1,
        "score":"3",
        "start":1,
        "dot":[
            46,
            356
        ],
        "height":229.44094488188978,
        "width":681,
        "every_height":48,
        "every_width":681,
        "padding":0,
        "show_title":1,
        "every_score":[
            3,
            2,
            1,
            0
        ],
        "total_score":"3",
        "index":0,
        "score_height":25.118110236220474,
        "score_width":110.82677165354332,
        "score_dot":[
            619.1732283464567,
            379.34645669291336
        ],
        "page":1
    },
    {
        "type":"answer",
        "name":"3",
        "num":1,
        "score":"3",
        "start":2,
        "dot":[
            46,
            564.6535433070866
        ],
        "height":208.65354330708664,
        "width":681,
        "every_height":48,
        "every_width":681,
        "padding":0,
        "show_title":0,
        "every_score":[
            3,
            2,
            1,
            0
        ],
        "total_score":"3",
        "index":1,
        "score_height":25.118110236220474,
        "score_width":110.82677165354332,
        "score_dot":[
            619.1732283464567,
            608.7874015748032
        ],
        "page":1
    }
]

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