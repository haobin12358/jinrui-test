import os, cv2
import fitz

pdf_dir = []

path = "C:\\Users\\Administrator\\Desktop\\jinrui\\math"
sheet_json = [
  {
    "type":"select",
    "name":"选择题",
    "num":10,
    "score":"3",
    "start":1,
    "dot":[83.259,355.949],
    "height":83.56940509915015,
    "width":521.81,
    "every_height":15.11,
    "every_width":119.8,
    "padding":5.67,
    "total_score":30,
    "index":0,
    "page":1
  },
  {
    "type":"fill",
    "name":"填空题",
    "num":1,
    "score":"4;2;0",
    "start":11,
    "dot":[33.99,355.51940509915016],
    "height":38.243626062322946,
    "width":521.81,
    "every_height":22.6628895184136,
    "every_width":521.81,
    "padding":0,
    "every_score":[4,2,0],
    "total_score":4,
    "index":1,
    "score_height":4,
    "score_width":27,
    "score_dot":[611.8927478753541,352.6865439093485],
    "page":1
  },
  {
    "type":"fill",
    "name":"填空题",
    "num":1,
    "score":"4;0",
    "start":12,
    "dot":[33.99,393.7630311614731],
    "height":38.243626062322946,
    "width":521.81,
    "every_height":22.6628895184136,
    "every_width":521.81,
    "padding":0,
    "every_score":[4,0],
    "total_score":4,
    "index":2,
    "score_height":4,
    "score_width":18,
    "score_dot":[637.3884985835693,390.93016997167143],
    "page":1
  },
  {
    "type":"fill",
    "name":"填空题",
    "num":1,
    "score":"4;0",
    "start":13,
    "dot":[33.99,432.0066572237961],
    "height":38.243626062322946,
    "width":521.81,
    "every_height":22.6628895184136,
    "every_width":521.81,
    "padding":0,
    "every_score":[4,0],
    "total_score":4,
    "index":3,
    "score_height":4,
    "score_width":18,
    "score_dot":[637.3884985835693,429.1737960339944],
    "page":1
  },
  {
    "type":"fill",
    "name":"填空题",
    "num":1,
    "score":"4;0",
    "start":14,
    "dot":[33.99,470.25028328611904],
    "height":38.243626062322946,
    "width":521.81,
    "every_height":22.6628895184136,
    "every_width":521.81,
    "padding":0,
    "every_score":[4,0],
    "total_score":4,
    "index":4,
    "score_height":4,
    "score_width":18,
    "score_dot":[637.3884985835693,467.41742209631735],
    "page":1
  },
  {
    "type":"fill",
    "name":"填空题",
    "num":1,
    "score":"4;0",
    "start":15,
    "dot":[33.99,508.493909348442],
    "height":38.243626062322946,
    "width":521.81,
    "every_height":22.6628895184136,
    "every_width":521.81,
    "padding":0,
    "every_score":[4,0],
    "total_score":4,
    "index":5,
    "score_height":4,
    "score_width":18,
    "score_dot":[637.3884985835693,505.6610481586403],
    "page":1
  },
  {
    "type":"fill",
    "name":"填空题",
    "num":1,
    "score":"4;0",
    "start":16,
    "dot":[33.99,546.737535410765],
    "height":38.243626062322946,
    "width":521.81,
    "every_height":22.6628895184136,
    "every_width":521.81,
    "padding":0,
    "every_score":[4,0],
    "total_score":4,
    "index":6,
    "score_height":4,
    "score_width":18,
    "score_dot":[637.3884985835693,543.9046742209632],
    "page":1
  },
  {
    "type":"answer",
    "name":"解答题",
    "num":1,
    "score":"6",
    "start":17,
    "dot":[33.99,584.9811614730879],
    "height":180.38404178648648,
    "width":521.81,
    "every_height":135.97733711048159,
    "every_width":521.81,
    "padding":0,
    "every_score":[6,5,4,3,2,1,0],
    "total_score":"6",
    "index":7,
    "score_height":4,
    "score_width":63,
    "score_dot":[509.9097450424929,582.1483002832862],
    "page":1
  },
  {
    "type":"answer",
    "name":"解答题",
    "num":1,
    "score":"6",
    "start":18,
    "dot":[33.99,53.8243626062323],
    "height":226.05233300747105,
    "width":521.81,
    "every_height":135.97733711048159,
    "every_width":521.81,
    "padding":0,
    "every_score":[6,5,4,3,2,1,0],
    "total_score":"6",
    "index":8,
    "score_height":4,
    "score_width":63,
    "score_dot":[509.9097450424929,762.5323420697727],
    "page":2
  },
  {
    "type":"answer",
    "name":"解答题",
    "num":1,
    "score":"6",
    "start":19,
    "dot":[33.99,279.87669561370336],
    "height":204.64532149763454,
    "width":521.81,
    "every_height":135.97733711048159,
    "every_width":521.81,
    "padding":0,
    "every_score":[6,5,4,3,2,1,0],
    "total_score":"6",
    "index":9,
    "score_height":4,
    "score_width":63,
    "score_dot":[509.9097450424929,1036.393667449212],
    "page":2
  },
  {
    "type":"answer",
    "name":"解答题",
    "num":1,
    "score":"8",
    "start":20,
    "dot":[33.99,484.5220171113379],
    "height":283.13769703370184,
    "width":521.81,
    "every_height":135.97733711048159,
    "every_width":521.81,
    "padding":0,
    "every_score":[8,7,6,5,4,3,2,1,0],
    "total_score":"8",
    "index":10,
    "score_height":4,
    "score_width":81,
    "score_dot":[458.9182436260623,1241.0389889468465],
    "page":2
  },
  {
    "type":"answer",
    "name":"解答题",
    "num":1,
    "score":"8",
    "start":21,
    "dot":[33.99,53.8243626062323],
    "height":326.6652871037027,
    "width":521.81,
    "every_height":135.97733711048159,
    "every_width":521.81,
    "padding":0,
    "every_score":[8,7,6,5,4,3,2,1,0],
    "total_score":"8",
    "index":11,
    "score_height":4,
    "score_width":81,
    "score_dot":[458.9182436260623,1524.1766859805484],
    "page":3
  },
  {
    "type":"answer",
    "name":"解答题",
    "num":1,
    "score":"10",
    "start":22,
    "dot":[33.99,380.489649709935],
    "height":382.3235170292776,
    "width":521.81,
    "every_height":135.97733711048159,
    "every_width":521.81,
    "padding":0,
    "every_score":[1,"",9,8,7,6,5,4,3,2,1,0],
    "total_score":"10",
    "index":12,
    "score_height":4,
    "score_width":108,
    "score_dot":[382.43099150141643,1850.841973084251],
    "page":3
  },
  {
    "type":"answer",
    "name":"解答题",
    "num":1,
    "score":"10",
    "start":23,
    "dot":[33.99,53.8243626062323],
    "height":355.20796911681816,
    "width":521.81,
    "every_height":135.97733711048159,
    "every_width":521.81,
    "padding":0,
    "every_score":[1,"",9,8,7,6,5,4,3,2,1,0],
    "total_score":"10",
    "index":13,
    "score_height":4,
    "score_width":108,
    "score_dot":[382.43099150141643,2233.1654901135284],
    "page":4
  },
  {
    "type":"answer",
    "name":"解答题",
    "num":1,
    "score":"12",
    "start":24,
    "dot":[33.99,409.03233172305045],
    "height":350.92656681485084,
    "width":521.81,
    "every_height":135.97733711048159,
    "every_width":521.81,
    "padding":0,
    "every_score":["1","",9,8,7,6,5,4,3,2,1,0],
    "total_score":"12",
    "index":14,
    "score_height":4,
    "score_width":108,
    "score_dot":[382.43099150141643,2588.3734592303467],
    "page":4
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
width_less = -25
height_less = 0

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
            sn_w = 630 + width_less
            sn_y = 37.795 + height_less
            sn_height = 16
            sn_width = 135
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
            sn_w = 574.016 + width_less
            sn_y = 140.822 + height_less
            sn_height = 215
            sn_width = 205
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
                        (select_y + sheet["every_height"]) * index_h),
                               int(select_x * index_w): int(
                                   (select_x + sheet["every_width"]) * index_w)]
                    label2picture(crop_img, "{0}-{1}-{2}-{3}".format(sheet["type"], str(int(i / 4)),
                                                                     str(sheet["index"] + 1), str(1)), name)

                    i = i + 4
                    jpg_name = name + "-" + str(i + page) + ".jpg"

# 剪裁ocr填空
def cut_fill_ocr():
    pass

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
                        (select_y + sheet["every_height"]) * index_h),
                               int(select_x * index_w): int(
                                   (select_x + sheet["every_width"]) * index_w)]
                    label2picture(crop_img, "{0}-{1}-{2}-{3}".format(sheet["type"], str(int(i / 4)),
                                                                     str(sheet["index"] + 1), str(1)), name)

                    i = i + 4
                    jpg_name = name + "-" + str(i + page) + ".jpg"

# 剪裁ocr简答
def cut_answer_ocr():
    pass


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