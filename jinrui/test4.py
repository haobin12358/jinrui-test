import requests, json, ctypes, oss2, uuid
from jinrui.config.secret import ALIOSS_BUCKET_NAME, ALIOSS_ENDPOINT, ACCESS_KEY_ID, ACCESS_KEY_SECRET

auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, ALIOSS_ENDPOINT, ALIOSS_BUCKET_NAME)
zip_uuid = str(uuid.uuid1())
ppt_url = "https://" + ALIOSS_BUCKET_NAME + "." + ALIOSS_ENDPOINT + "/" + "testA" + zip_uuid + ".zip"
result = bucket.put_object_from_file("testA" + zip_uuid + ".zip", "C:\\Users\\Administrator\\Desktop\\jinrui\\math\\test_answer\\" + "testA.zip")
print(result)
print(ppt_url)