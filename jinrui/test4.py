import requests, json
picture_json = {
 '19': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/answerocr-0-10-1_5844315876036608.jpg',
 '20': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/answerocr-0-11-1_5844317100773376.jpg',
 '21': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/answerocr-0-12-1_5844318401007616.jpg',
 '22': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/answerocr-0-13-1_5844319822876672.jpg',
 '23': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/answerocr-0-14-1_5844321232162816.jpg',
 '24': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/answerocr-0-15-1_5844322465288192.jpg',
 '17': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/answerocr-0-8-1_5844323975237632.jpg',
 '18': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/answerocr-0-9-1_5844325367746560.jpg',
 '11': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/fillocr-0-2-1_5844338005184512.jpg',
 '12': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/fillocr-0-3-1_5844339171201024.jpg',
 '13': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/fillocr-0-4-1_5844340169445376.jpg',
 '14': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/fillocr-0-5-1_5844341092192256.jpg',
 '15': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/fillocr-0-6-1_5844342040104960.jpg',
 '16': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/fillocr-0-7-1_5844343076098048.jpg',
 '1': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/select-0-1-1_5844347178127360.jpg',
 '10': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/select-0-1-10_5844348256063488.jpg',
 '2': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/select-0-1-2_5844349296250880.jpg',
 '3': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/select-0-1-3_5844350328049664.jpg',
 '4': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/select-0-1-4_5844351309516800.jpg',
 '5': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/select-0-1-5_5844352290983936.jpg',
 '6': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/select-0-1-6_5844353335365632.jpg',
 '7': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/select-0-1-7_5844354346192896.jpg',
 '8': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/select-0-1-8_5844355340242944.jpg',
 '9': 'https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/select-0-1-9_5844356439150592.jpg',
}

sn = "https://jinrui-sheet.oss-cn-shanghai.aliyuncs.com/sn-0_5844357689053184.jpg"

type_json = {
    "1": 1,
    "2": 1,
    "3": 1,
    "4": 1,
    "5": 1,
    "6": 1,
    "7": 1,
    "8": 1,
    "9": 1,
    "10": 1,
    "11": 4,
    "12": 4,
    "13": 4,
    "14": 4,
    "15": 4,
    "16": 4,
    "17": 5,
    "18": 5,
    "19": 5,
    "20": 5,
    "21": 5,
    "22": 5,
    "23": 5,
    "24": 5,
}

point_json  = {
    "1": [3],
    "2": [3],
    "3": [3],
    "4": [3],
    "5": [3],
    "6": [3],
    "7": [3],
    "8": [3],
    "9": [3],
    "10": [3],
    "11": [4,2,0],
    "12": [4,0],
    "13": [4,0],
    "14": [4,0],
    "15": [4,0],
    "16": [4,0],
    "17": [6],
    "18": [6],
    "19": [6],
    "20": [8],
    "21": [8],
    "22": [10],
    "23": [10],
    "24": [12],
}

url = "https://api.hayuea.com:8000/ocr/analyze/answer"
for key in picture_json:

    post_dict = {
        "paperId": sn,
        "imgUrl": picture_json[key],
        "imgType": type_json[key],
        "point": point_json[key],
        "notificationUrl": "https://jinrui.sanbinit.cn/api/ocr/mock_ocr_response?key=eyJhbGciOiJIUzI1NiIsImlhdCI6MTYwMjY1Njk1OCwiZXhwIjoxNjAzMjYxNzU4fQ.eyJ1c2VybmFtZSI6Ilx1OTBkZFx1NjU4YyIsImlkIjoiNWI0NmYyNjItZjBkOS0xMWVhLWFiMGUtNGNlZGZiNzk1OGEyIiwibW9kZWwiOiJVc2VyIiwibGV2ZWwiOiIwIn0.Bpy-Z0xuB1_1L8-KOkYUbws9faoDc9nfy6rArl8W7jM"
    }
    response = requests.post(url=url, json=post_dict)
    content = json.loads(response.content)
    if content["status"] == 200:
        print("success test:>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" + key)
    else:
        print("error test:>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" + key + ":" + str(content["status"]))