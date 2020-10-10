from PIL import Image
import os
import cv2
import time

use_json = []

def label2picture(cropImg, framenum, tracker):
    pathnew = "D:\\img2\\"
    # cv2.imshow("image", cropImg)
    # cv2.waitKey(1)
    if (os.path.exists(pathnew + tracker)):
        print(">>>>>>>>>>>>>>>>>" + framenum)
        cv2.imwrite(pathnew + tracker + '\\' + framenum + '.jpg', cropImg, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

    else:
        os.makedirs(pathnew + tracker)
        cv2.imwrite(pathnew + tracker + '\\' + framenum + '.jpg', cropImg, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

img = cv2.imread(os.getcwd() + "\\ocr1.jpg")
print(len(img[1]))
index_h = 0.353 / 357 * 1682 * 1.2
index_w = 0.353 / 250 * 1183 * 1.2
i = 1
sn_w = 432
sn_y = 41
sn_height = 4 / 0.353
sn_width = 39 /0.353 - 30
crop_img = img[int(sn_y * index_h): int((sn_y + sn_height) * index_h), int(sn_w * index_w): int((sn_w + sn_width) * index_w)]
label2picture(crop_img, "sn", "test")
no_w = 380.08
no_y = 127.31
no_height = 64 / 0.353 - 48
no_width = 77 / 0.353 - 45
crop_img = img[int(no_y * index_h): int((no_y + no_height) * index_h),
           int(no_w * index_w): int((no_w + no_width) * index_w)]
label2picture(crop_img, "no", "test")
for row in use_json:

    # img_orc = cv2.imread("D:\\img2\\test\\ocrtest.jpg")
    if row["page"] == 5:
        if row["type"] == "select":
            j = 0
            row["every_width"] = row["every_width"] + 10
            row["every_height"] = row["every_height"] - 0.7
            while j < row["num"]:
                left = (int(j / 5)) * row["every_width"] + 3
                print(left)
                up = 7.5 / 0.363 + (j % 5) * row["every_height"] + 10
                print(up)
                crop_img = img[int((row["dot"][1] + up) * index_h): int((row["dot"][1] + row["every_height"] + up) * index_h), int((row["dot"][0] + left) * index_w): int((row["dot"][0] + left + row["every_width"]) * index_w)]
                print("left:start:" + str(int((row["dot"][0] + left) * index_w)))
                print("up:start" + str(int((row["dot"][1] + up) * index_h)))
                print("left:end:" + str(int((row["dot"][0] + left + row["every_width"]) * index_w)))
                print("up:end" + str(int((row["dot"][1] + row["every_height"] + up) * index_h)))
                label2picture(crop_img, "{2}-{3}-{0}-{1}".format(str(i), str(j), row["type"], row["index"]), "test")
                j = j + 1
        elif row["type"] == "multi":
            j = 0
            row["every_width"] = row["every_width"] + 10
            row["every_height"] = row["every_height"] - 0.7
            while j < row["num"]:
                left = (int(j / 5)) * row["every_width"] + 3
                print(left)
                up = 7.5 / 0.363 + (j % 5) * row["every_height"] - 5
                print(up)
                crop_img = img[
                           int((row["dot"][1] + up) * index_h): int((row["dot"][1] + row["every_height"] + up) * index_h),
                           int((row["dot"][0] + left) * index_w): int(
                             (row["dot"][0] + left + row["every_width"]) * index_w)]
                print("left:start:" + str(int((row["dot"][0] + left) * index_w)))
                print("up:start" + str(int((row["dot"][1] + up) * index_h)))
                print("left:end:" + str(int((row["dot"][0] + left + row["every_width"]) * index_w)))
                print("up:end" + str(int((row["dot"][1] + row["every_height"] + up) * index_h)))
                label2picture(crop_img, "{2}-{3}-{0}-{1}".format(str(i), str(j), row["type"], row["index"]), "test")
                j = j + 1
        elif row["type"] == "judge":
            j = 0
            row["every_width"] = row["every_width"] + 2
            row["every_height"] = row["every_height"] - 0.7
            while j < row["num"]:
                left = (int(j / 5)) * row["every_width"] + 2
                print(left)
                up = 7.5 / 0.363 + (j % 5) * row["every_height"] - 6
                print(up)
                crop_img = img[
                           int((row["dot"][1] + up) * index_h): int((row["dot"][1] + row["every_height"] + up) * index_h),
                           int((row["dot"][0] + left) * index_w): int(
                             (row["dot"][0] + left + row["every_width"]) * index_w)]
                print("left:start:" + str(int((row["dot"][0] + left) * index_w)))
                print("up:start" + str(int((row["dot"][1] + up) * index_h)))
                print("left:end:" + str(int((row["dot"][0] + left + row["every_width"]) * index_w)))
                print("up:end" + str(int((row["dot"][1] + row["every_height"] + up) * index_h)))
                label2picture(crop_img, "{2}-{3}-{0}-{1}".format(str(i), str(j), row["type"], row["index"]), "test")
                j = j + 1

        elif row["type"] == "fill":
            start_w = row["dot"][0] + row["every_width"] - len(row["every_score"]) * 9 / 0.353 - 22
            start_y = row["dot"][1] + 20
            width = len(row["every_score"]) * 9 / 0.353 - 17
            height = row["every_height"]
            crop_img = img[
                int(start_y * index_h): int((start_y + height) * index_h),
                int(start_w * index_w): int((start_w + width) * index_w)
            ]
            label2picture(crop_img, "{0}-{2}-{1}".format(row["type"], str(i), row["index"]), "test")
        elif row["type"] == "answer":
            start_w = row["dot"][0] + row["every_width"] - len(row["every_score"]) * 9 / 0.353 + 58
            start_y = row["dot"][1] + 23
            width = len(row["every_score"]) * 9 / 0.353 - 85
            height = 4 / 0.353
            crop_img = img[
                       int(start_y * index_h): int((start_y + height) * index_h),
                       int(start_w * index_w): int((start_w + width) * index_w)
                       ]
            label2picture(crop_img, "{0}-{2}-{1}".format(row["type"], str(i), row["index"]), "test")
        else:
            crop_img = img[int(row["dot"][1] * index_h): int(row["dot"][1] * index_h + row["height"] * index_h), int(row["dot"][0] * index_w): int(row["dot"][0] * index_w + row["width"] * index_w)]
            # crop_img = img[int(439.0888101983003 * 2): int(2*(439.0888101983003 + 83.56940509915015)), int(2 * 33.99): int(2*(33.99 + 521.81))]
            label2picture(crop_img, "ocrtest{0}".format(str(i)), "test")
            # img_orc = cv2.imread("D:\\img2\\test\\ocrtest.jpg")
        i = i + 1