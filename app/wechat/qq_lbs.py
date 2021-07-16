from app import redis_db
import json
import datetime
import requests
from app.wechat.wechat_config import LBS_KEY, LBS_COORDINATE_URL
from app.public_method import success_return, false_return


def lbs_get_by_coordinate(lat, lng, detail=None):
    try:
        if redis_db.exists('access_token'):
            token = json.loads(redis_db.get('access_token'))
            if datetime.datetime.now().timestamp() <= token['now_time'] + token['expires_in']:
                return token['access_token']

        params = {"location": f"{lat},{lng}", "key": LBS_KEY}
        req = requests.get(LBS_COORDINATE_URL, params=params)
        if req.status_code != 200:
            raise Exception("请求接口失败, request返回值非200")
        content = req.json()
        if content['status'] != 0:
            raise Exception(content['message'])
        address = content['result']['address_component']
        if address['province'] != address['city']:
            # addr_join = address['nation'] + address['province'] + address['city'] + address['district']
            addr = [address['nation'], address['province'], address['city'], address['district']]
        else:
            addr = [address['nation'], address['province'], address['district']]
        return success_return(data=addr) if detail is None else success_return(
            data=content['result']['address_component'])
    except Exception as e:
        return false_return(message=str(e))


if __name__ == "__main__":
    print(lbs_get_by_coordinate("39.984154", "116.307490"))
