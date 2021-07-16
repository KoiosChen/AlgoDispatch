from app.wechat.access_token import get_token
from app.wechat.wechat_config import upload_url
import requests
import json


def upload(media, media_type):
    token = get_token()
    params = {"access_token": token, "type": media_type}
    req = requests.post(upload_url, data=params, files={'file': media})
    return json.loads(req.content.decode())


if __name__ == "__main__":
    with open("/Users/Peter/Downloads/insurance_msg.jpg", "rb") as f:
        upload(f, "image")
