import requests
from app.wechat.wechat_config import app_id, app_secret, login_url


class WxLogin(object):
    def __init__(self, jscode):
        __params = {"appid": app_id, "secret": app_secret, "js_code": jscode,
                    "grant_type": "authorization_code"}
        r = requests.get(login_url, params=__params)
        self.response = r.json()

    def get_openid(self):
        return self.response.get('openid')

    def get_session_key(self):
        return self.response.get('session_key')
