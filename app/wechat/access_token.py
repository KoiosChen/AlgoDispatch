from app import redis_db
import json
import datetime
import requests
from app.wechat.wechat_config import app_id, app_secret, access_token_url


def get_token():
    if redis_db.exists('access_token'):
        token = json.loads(redis_db.get('access_token'))
        if datetime.datetime.now().timestamp() <= token['now_time'] + token['expires_in']:
            return token['access_token']

    params = {"grant_type": "client_credential", "appid": app_id, "secret": app_secret}
    req = requests.get(access_token_url, params=params)
    content = req.json()
    content['now_time'] = datetime.datetime.now().timestamp()
    redis_db.set('access_token', json.dumps(content), ex=content.get('expires_in'))
    return content.get('access_token')


if __name__ == "__main__":
    get_token()
