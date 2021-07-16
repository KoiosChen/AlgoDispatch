#!/usr/bin/env python
# -*- coding: utf-8 -*-
from app import logger, redis_db, db
from app.models import ShopOrders, make_order_id
from . import wechat
from app.wechat.wechat_config import WEIXIN_APP_ID, WEIXIN_MCH_ID, WEIXIN_SIGN_TYPE, WEIXIN_SPBILL_CREATE_IP, \
    WEIXIN_BODY, \
    WEIXIN_KEY, WEIXIN_UNIFIED_ORDER_URL, WEIXIN_QUERY_ORDER_URL, WEIXIN_CALLBACK_API
import traceback
import xmltodict
from flask import request, jsonify
from hashlib import md5
from app.public_method import session_commit, new_data_obj
import datetime
from app.rebates import calc_rebate
from .update_order import update_order


@wechat.route('/wechat_pay/callback/', methods=['POST', 'GET'])
def wechat_pay_callback():
    if request.method == 'GET':
        return 'GOT'
    else:
        return weixin_rollback(request)


def weixinpay_call_back(request):
    """
    微信支付回调
    :param request: 回调参数
    :return:
    """

    def generate_sign(params):
        """
        生成md5签名的参数
        """
        if 'sign' in params:
            params.pop('sign')
        src = '&'.join(['%s=%s' % (k, v) for k, v in sorted(params.items(), key=lambda d: d[0]) if
                        k != "#text"]) + '&key=%s' % WEIXIN_KEY
        print(src)
        return md5(src.encode('utf-8')).hexdigest().upper()

    def validate_sign(resp_dict):
        """
        验证微信返回的签名
        """
        if 'sign' not in resp_dict:
            return False
        wx_sign = resp_dict['sign']
        sign = generate_sign(resp_dict)
        if sign == wx_sign:
            return True
        return False

    def handle_wx_response_xml():
        """
        处理微信支付返回的xml格式数据
        """
        resp_dict = xmltodict.parse(args)['xml']
        return_code = resp_dict.get('return_code')
        if return_code == 'SUCCESS':  # 仅仅判断通信标识成功，非交易标识成功，交易需判断result_code
            if validate_sign(resp_dict):
                return resp_dict
        else:
            print('FAIL')
        return

    args = request.data
    logger.debug(f"The respond data is {args}")
    # 验证平台签名
    resp_dict = handle_wx_response_xml()
    logger.debug(f"The respond dict of the callback is {resp_dict}")
    # resp_dict = request.json
    if resp_dict is None:
        return None
    return resp_dict


def weixinpay_response_xml(params):
    """
    生成交易成功返回信息
    """

    def generate_response_data(resp_dict):
        """
        字典转xml
        """
        return xmltodict.unparse({'xml': resp_dict}, pretty=True, full_document=False).encode('utf-8')

    return_code = 'SUCCESS' if params == 'success' else 'FAIL'
    return_msg = 'OK' if params == 'success' else params
    return_info = {
        'return_code': return_code,
        'return_msg': return_msg
    }
    return generate_response_data(return_info)


def create_cargoes(**kwargs):
    """
    如果是需要仓储，有分装（分发）流程的货物，则产生仓储记录
    :param kwargs:
    :return:
    """
    pass


def weixin_rollback(request):
    """
    【API】: 微信支付结果回调接口,供微信服务端调用
    """
    try:
        # 支付异步回调验证
        data = weixinpay_call_back(request)
        res = update_order(data)
    except Exception as e:
        logger.error(str(e))
        traceback.print_exc()
        res = str(e)
    finally:
        logger.debug(res)
        return weixinpay_response_xml(res)
