# -*- coding: utf-8 -*-
from app import logger
from app.wechat.wechat_config import app_id, WEIXIN_MCH_ID, WEIXIN_SIGN_TYPE, WEIXIN_KEY, WEIXIN_REFUND_API, \
    WEIXIN_REFUND_CALLBACK_API
import uuid
import xmltodict
from hashlib import md5


def generate_sign(params):
    """
    生成md5签名的参数
    """
    if 'sign' in params:
        params.pop('sign')
    src = '&'.join(['%s=%s' % (k, v) for k, v in sorted(params.items())]) + '&key=%s' % WEIXIN_KEY
    logger.debug(src.encode('utf-8'))
    return md5(src.encode('utf-8')).hexdigest().upper()


def generate_nonce_str():
    """
    生成随机字符串
    """
    return str(uuid.uuid4()).replace('-', '')


def generate_request_data(params_dict):
    """
    生成统一下单请求所需要提交的数据
    """
    params_dict['nonce_str'] = generate_nonce_str()
    params_dict['sign'] = generate_sign(params_dict)
    return xmltodict.unparse({'xml': params_dict}, pretty=True, full_document=False).encode('utf-8')
