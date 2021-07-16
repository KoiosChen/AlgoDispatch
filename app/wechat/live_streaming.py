from app.wechat.wechat_config import app_id, app_secret, broadcast_url, upload_url, access_token_url
from app.wechat.access_token import get_token
import datetime
import requests
from app import logger, redis_db
import json


def create_room(**room_info):
    req = requests.post(broadcast_url, json={key: value for key, value in room_info.items()},
                        data={'access_token': get_token()})
    print(req.content)


if __name__ == "__main__":
    info = {"name": "broadcasting test",
            "coverImg": "fl97cY-_i0V_Fi1Ma857sQoZNLfKnnSsdibu6LFqqOk1XqnHtaFbYt9aV7ZNVClK",
            "startTime": int(
                datetime.datetime.strptime("2020-08-08 12:00:00", '%Y-%m-%d %H:%M:%S').timestamp()),
            "endTime": int(
                datetime.datetime.strptime("2020-08-08 13:00:00", '%Y-%m-%d %H:%M:%S').timestamp()),
            "anchorName": "Peter",
            "anchorWechat": "solomon_chen",
            "shareImg": "fl97cY-_i0V_Fi1Ma857sQoZNLfKnnSsdibu6LFqqOk1XqnHtaFbYt9aV7ZNVClK",
            "screenType": 0,
            "closeLike": 0,
            "closeGoods": 1,
            "closeComment": 0
            }

    create_room(**info)
