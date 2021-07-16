# -*- coding: utf-8 -*-
from app.wechat.wechat_config import app_id, WEIXIN_MCH_ID, WEIXIN_SIGN_TYPE, WEIXIN_SPBILL_CREATE_IP, WEIXIN_BODY, \
    WEIXIN_KEY, \
    WEIXIN_UNIFIED_ORDER_URL, WEIXIN_QUERY_ORDER_URL, WEIXIN_CALLBACK_API
import traceback
import xmltodict
import uuid
import json
import requests
from hashlib import md5
from app.models import ShopOrders
from app import logger
from app.wechat import update_order


def make_querypayment_request(params_dict, query_order_url):
    """
    生成查询订单返回的数据参数
    """

    def generate_nonce_str():
        """
        生成随机字符串
        """
        return str(uuid.uuid4()).replace('-', '')

    def generate_sign(params):
        """
        生成md5签名的参数
        """
        if 'sign' in params:
            params.pop('sign')
        src = '&'.join(['%s=%s' % (k, v) for k, v in sorted(params.items())]) + '&key=%s' % WEIXIN_KEY
        return md5(src.encode('utf-8')).hexdigest().upper()

    def generate_request_data(params_dict):
        """
        生成统一下单请求所需要提交的数据
        """
        params_dict['nonce_str'] = generate_nonce_str()
        params_dict['sign'] = generate_sign(params_dict)
        return xmltodict.unparse({'xml': params_dict}, pretty=True, full_document=False).encode('utf-8')

    data = generate_request_data(params_dict)
    headers = {'Content-Type': 'application/xml'}
    res = requests.post(query_order_url, data=data, headers=headers)
    if res.status_code == 200:
        result = json.loads(json.dumps(xmltodict.parse(res.content)))
        # if result['xml']['return_code'] == 'SUCCESS':
        #     prepay_id = result['xml']['prepay_id']
        #     return generate_call_app_data(params_dict, prepay_id)
        # else:
        return result['xml']
    return None


def weixin_orderquery(out_trade_no):
    """
    【API】:支付状态查询,供商户客户端app调用
    """
    res = {
        'code': 1,
        'status': 0,
        'msg': '支付失败！未知错误！'
    }

    try:
        order_data = ShopOrders.query.get(out_trade_no)
        if order_data:
            # 支付成功
            if order_data.is_pay == 1:
                res['status'] = 1
                res['msg'] = '支付成功!'
            # 支付失败
            elif order_data.is_pay == 0:
                res['status'] = 0
                res['msg'] = '支付失败!'
            # 支付过程中, 查询微信服务器支付状态
            else:
                params_dict = {
                    'appid': app_id,
                    'mch_id': WEIXIN_MCH_ID,
                    'transaction_id': order_data.transaction_id
                }
                data = make_querypayment_request(params_dict, WEIXIN_QUERY_ORDER_URL)
                if data:
                    if data['return_code'] == 'SUCCESS':
                        res = update_order.update_order(data)
                    else:
                        res['status'] = 0
                        res['msg'] = data['err_code_des']
                else:
                    res['msg'] = "支付错误! 微信服务器通信错误！"
        else:
            res['status'] = 0
            res['msg'] = "订单号不存在！"
    except Exception:
        traceback.print_exc()
    finally:
        logger.debug(res)
        return json.dumps(res)
