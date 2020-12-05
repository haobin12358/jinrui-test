import oss2, uuid, requests
from testsecret import ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME, ACCESS_KEY_SECRET, ACCESS_KEY_ID

auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)

file_uuid = str(uuid.uuid1())
file_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + "file-" + file_uuid + ".pdf"
file_path = "D:\\test.pdf"
result = bucket.put_object_from_file("file-" + file_uuid + ".pdf", file_path)
if result.status != 200:
    print("oss上传失败")
else:
    body_dict = {
        "file": file_url,
        "paper_name": "中考模拟卷（数学）",
        "pdf_use": "300201"
    }
    url = "https://jinrui.sanbinit.cn/api/ocr/mock_pdf"
    result = requests.post(url=url, json=body_dict)
    print(result.content)