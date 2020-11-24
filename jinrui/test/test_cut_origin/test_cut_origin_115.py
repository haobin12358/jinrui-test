"""
测试模块1：
    测试非矫正之后的原始图像坐标
"""

import requests
import json
import os
import cv2
import time

url = "https://jinrui.sanbinit.cn/api/ocr/get_pdf"


def path_change_test(origin_path, local_path):
    """
    将网络图像路径转化为本地图像路径
    """
    local_list = os.listdir(local_path)

    ext_name = os.path.basename(origin_path).split("-")[-1]
    for local_name in local_list:
        local_ext = local_name.split("-")[-1]
        # if ext_name == "0001.png":
        #     return os.path.join(local_path, local_name)
        # else:
        #     return ""
        if local_ext == ext_name:
            return os.path.join(local_path, local_name)


def get_data(local_path="", code=300306):
    """
    从接口获取原生json数据
    """
    data = {'pdf_status': code}
    pdf_data = requests.get(url, params=data).json()
    return get_json_dict(pdf_data, local_path=local_path)


def get_json_dict(pdf_data, local_path=""):
    """
    从接口数据解析出图像路径以及json_dict
    """
    if len(pdf_data) == 0:
        return [], []
    img_paths = []
    json_dict = []
    for pdf in pdf_data:
        if len(local_path) == 0:
            img_paths.append(pdf['jpg_path'])
        else:
            img_paths.append(path_change_test(pdf['jpg_path'], local_path))
        json_dict.append(pdf['json_dict'])
    return img_paths, json_dict


def get_pts(json_dict):
    """
    从单个json_dict中提取需要的坐标信息
    """
    if len(json_dict) == 0:
        return
    ocr_dict = json_dict['ocr_dict']
    height = json_dict['height']
    width = json_dict['width']

    pts = []
    for ocr in ocr_dict:
        cut_dot = ocr['cut_dot']
        cut_height = ocr['cut_height']
        cut_width = ocr['cut_width']

        ocr_dot = ocr['ocr_dot']
        ocr_height = ocr['ocr_height']
        ocr_width = ocr['ocr_width']

        # None 错误检测
        if cut_dot is None:
            cut_dot = [0, 0]
        if cut_height is None:
            cut_height = 0
        if cut_width is None:
            cut_width = 0

        if ocr_dot is None:
            ocr_dot = [0, 0]
        if ocr_height is None:
            ocr_height = 0
        if ocr_width is None:
            ocr_width = 0

        ocr_type = float(ocr['type'])

        img_use = float(ocr['img_use'])

        index = ocr['index']
        if index is not None:
            index = float(index)
        else:
            if ocr_type == 20:
                index = -2
            elif ocr_type == 28:
                index = -3
            elif ocr_type == 29:
                index = -4
            else:
                index = -1
        pts.append([
            width, height, cut_dot[0], cut_dot[1], cut_width, cut_height,
            ocr_dot[0], ocr_dot[1], ocr_width, ocr_height, ocr_type, img_use,
            index
        ])
    return pts


def find_pts(bin_img, flag):
    """
        描述：二值图像，寻找黑块顶点
        参数：二值化图像，目标boudingbox顶点位置，1-左上角，2-左下角，3-右上角，4-右下角
        返回：顶点坐标
        """
    bin_img, contouts, hierarchy = cv2.findContours(bin_img, cv2.RETR_TREE,
                                                    cv2.CHAIN_APPROX_SIMPLE)
    if len(contouts) == 0:
        return []

    contouts = sorted(contouts, key=lambda x: cv2.contourArea(x), reverse=True)

    index = 0
    x, y, w, h = cv2.boundingRect(contouts[index])

    if flag == 1:
        return [int(x), int(y)]
    elif flag == 2:
        return [int(x), int(y + h)]
    elif flag == 3:
        return [int(x + w), int(y)]
    elif flag == 4:
        return [int(x + w), int(y + h)]
    else:
        return []


def compute_effect_area(img):
    """
    输入：简化版，计算四角点坐标
    """
    height, width, stride = img.shape
    rate = 8
    area_img = float(width * height)
    gray_min = 150
    gray_max = 255
    max_box = 0.9
    min_box = 0.001
    ercode_size = 3
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, img_bin = cv2.threshold(img_gray, gray_min, gray_max,
                               cv2.THRESH_BINARY_INV)
    struct_ele = cv2.getStructuringElement(cv2.MORPH_RECT,
                                           (ercode_size, ercode_size),
                                           (-1, -1))
    img_ercode = cv2.erode(img_bin, struct_ele, (-1, -1))

    img_left_top_bin = img_ercode[0:int(height / rate), 0:int(width / rate)]
    img_left_bottom_bin = img_ercode[int(height / rate *
                                         (rate - 1)):(int(height / rate *
                                                          (rate - 1)) +
                                                      int(height / rate)),
                                     0:int(width / rate)]
    img_right_top_bin = img_ercode[0:int(height / rate),
                                   int(width / rate *
                                       (rate - 1)):(int(width / rate *
                                                        (rate - 1)) +
                                                    int(width / rate))]
    img_right_bottom_bin = img_ercode[int(height / rate *
                                          (rate - 1)):(int(height / rate *
                                                           (rate - 1)) +
                                                       int(height / rate)),
                                      int(width / rate *
                                          (rate - 1)):(int(width / rate *
                                                           (rate - 1)) +
                                                       int(width / rate))]
    left_top_pts = find_pts(img_left_top_bin, 1)
    left_bottom_pts = find_pts(img_left_bottom_bin, 2)
    right_top_pts = find_pts(img_right_top_bin, 3)
    right_bottom_pts = find_pts(img_right_bottom_bin, 4)
    if len(left_top_pts) == 0:
        return [], [], [], []
    if len(left_bottom_pts) == 0:
        return [], [], [], []
    if len(right_top_pts) == 0:
        return [], [], [], []
    if len(right_bottom_pts) == 0:
        return [], [], [], []
    right_top_pts[0] = right_top_pts[0] + int(width / rate * (rate - 1))

    right_bottom_pts[0] = right_bottom_pts[0] + int(width / rate * (rate - 1))
    right_bottom_pts[1] = right_bottom_pts[1] + int(height / rate * (rate - 1))

    left_bottom_pts[1] = left_bottom_pts[1] + int(height / rate * (rate - 1))

    effect_area_width = right_top_pts[0] - left_top_pts[0]
    effect_area_height = left_bottom_pts[1] - left_top_pts[1]
    effect_area = [
        left_top_pts[0], left_top_pts[1], effect_area_width, effect_area_height
    ]

    return effect_area


def draw_img(img_path, pts, flag):
    """
    输入：img_path-原图路径，pts-数据，flag-1表示cut；2表示ocr
    功能：根据输入数据进行裁图
    """
    img = cv2.imread(img_path)
    effect_area = compute_effect_area(img)
    if len(effect_area) == 0:
        print("img's effect area is too samll")
        return []
    effect_area_x = effect_area[0]
    effect_area_y = effect_area[1]
    effect_area_width = effect_area[2]
    effect_area_height = effect_area[3]
    for p in pts:
        rate_width = p[0] / effect_area_width
        rate_height = p[1] / effect_area_height

        img = cv2.resize(
            img,
            (int(img.shape[1] * rate_width), int(img.shape[0] * rate_height)))

        effect_area_x = int(effect_area_x * rate_width)
        effect_area_y = int(effect_area_y * rate_height)
        effect_area_width = int(effect_area_width * rate_width)
        effect_area_height = int(effect_area_height * rate_height)

        new_cut_x = int(p[2] + effect_area_x)
        new_cut_y = int(p[3] + effect_area_y)
        new_ocr_x = int(p[6] + effect_area_x)
        new_ocr_y = int(p[7] + effect_area_y)

        cv2.circle(img, (effect_area_x, effect_area_y), 3, (0, 0, 255), 4)
        cv2.circle(img, (effect_area_x + effect_area_width, effect_area_y), 3,
                   (0, 0, 255), 4)
        cv2.circle(img, (effect_area_x, effect_area_y + effect_area_height), 3,
                   (0, 0, 255), 4)
        cv2.circle(img, (effect_area_x + effect_area_width,
                         effect_area_y + effect_area_height), 3, (0, 0, 255),
                   4)

        if flag == 1:
            cv2.rectangle(img, (int(new_cut_x), int(new_cut_y)),
                          (int(new_cut_x + p[4]), int(new_cut_y + p[5])),
                          (0, 0, 255))
        elif flag == 2:
            cv2.rectangle(img, (int(new_ocr_x), int(new_ocr_y)),
                          (int(new_ocr_x + p[8]), int(new_ocr_y + p[9])),
                          (0, 0, 255))
    return img


def save_img(img, origin_path, flag):
    """
    功能：存储最终图像
    """
    basename = os.path.basename(origin_path)
    target_dir = os.path.join(os.getcwd(), "new")
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)
    cut_target_dir = os.path.join(target_dir, "cut_draw")
    ocr_target_dir = os.path.join(target_dir, "ocr_draw")
    if not os.path.exists(cut_target_dir):
        os.mkdir(cut_target_dir)
    if not os.path.exists(ocr_target_dir):
        os.mkdir(ocr_target_dir)

    if flag == 1:
        save_path = os.path.join(cut_target_dir,
                                 basename.split(".")[0] + "_cut.png")
        cv2.imwrite(save_path, img)
    elif flag == 2:
        save_path = os.path.join(ocr_target_dir,
                                 basename.split(".")[0] + "_ocr.png")
        cv2.imwrite(save_path, img)


def aligner_cut():
    """
    功能：总入口
    """
    start_time = time.time()

    img_paths, json_dict = get_data(local_path="origin")
    print(len(img_paths),len(json_dict))
    network_time = time.time()

    print('network get cost time = %fs' % (network_time - start_time))

    for i in range(len(img_paths)):
        cut_time_start = time.time()
        img_path = img_paths[i]
        if len(img_path) == 0:
            print(f"not exists img_path {img_path}")
            continue
        pts=get_pts(json_dict[i])
        draw_cut = draw_img(img_path, pts, 1)
        draw_ocr = draw_img(img_path, pts, 2)
        if draw_cut is None or draw_ocr is None:
            print("cut failed")
            continue
        save_img(draw_cut, img_path, 1)
        save_img(draw_ocr, img_path, 2)


if __name__ == "__main__":
    aligner_cut()
