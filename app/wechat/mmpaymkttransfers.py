# -*- coding: utf-8 -*-
from app import db, redis_db, sku_lock
from app.models import ShopOrders, Benefits, ShoppingCart, PackingItemOrders, Customers, MemberRechargeRecords, \
    make_uuid, CERT_PATH, KEY_PATH
from app.wechat.wechat_config import WEIXIN_PURSE_API
import traceback
import requests
import json
import time
import datetime
from app.public_method import new_data_obj, calc_sku_price
from app.common import success_return, false_return, session_commit
from app.mall.sku import compute_quantity
import threading
from .public_method import *
from decimal import Decimal


def make_payment_info(partner_trade_no=None, amount=None, openid=None, device_info=None, check_name='NO_CHECK', desc='返佣提现'):
    order_info = {'mch_appid': app_id,
                  'mchid': WEIXIN_MCH_ID,
                  'device_info': "pay to purse",
                  'nonce_str': '',
                  'partner_trade_no': str(partner_trade_no),
                  'openid': openid,
                  'check_name': check_name,
                  'amount': amount,
                  'desc': desc}
    return order_info


def request_wx_pay(partner_trade_no, amount, openid):
    """
    微信统一下单，并返回客户端数据
    :param partner_trade_no: 订单编号
    :param amount: 提现金额
    :param openid: openid
    :return: app所需结果数据
    """
    def make_payment_request(params_dict, unified_order_url):
        """
        生成返回给客户端APP的数据参数
        """
        data = generate_request_data(params_dict)
        headers = {'Content-Type': 'application/xml'}
        req = requests.post(unified_order_url, data=data, headers=headers, cert=(CERT_PATH, KEY_PATH))
        if req.status_code == 200:
            result = json.loads(json.dumps(xmltodict.parse(req.content)))
            logger.debug(result)
            xml_content = result['xml']
            if xml_content['return_code'] == 'SUCCESS' and xml_content['result_code'] == 'SUCCESS':
                # 返回result
                return "SUCCESS", result['xml']
            elif xml_content['return_code'] == 'SUCCESS':
                return result['xml']['err_code'] + ": " + result['xml']['err_code_des'], None
            else:
                return result['xml']['return_code'] + ': ' + result['xml']['return_msg'], None
        return None, None

    if float(amount) < 0.01:
        raise Exception('金额不能小于0.01')

    # 返回统一下单接口请求参数
    payment_info = make_payment_info(partner_trade_no=partner_trade_no, amount=amount, openid=openid)

    # 统一下单接口提交请求
    res, info = make_payment_request(payment_info, WEIXIN_PURSE_API)
    return res, info


def weixin_pay_purse(order_id, amount, customer_id, check_name="NO_CHECK"):
    """
    【API】: 创建订单,供商户app调用
    """
    try:
        customer = db.session.query(Customers).with_for_update().filter(Customers.id.__eq__(customer_id)).first()
        amount = Decimal(str(amount))
        print(amount, customer.purse)
        if amount > customer.purse:
            raise Exception("取现金额大于账户余额")

        new_weixin_pay_purse_order = new_data_obj("WechatPurseTransfer",
                                                  **{"id": order_id,
                                                     "customer_id": customer_id,
                                                     "amount": amount})
        if not new_weixin_pay_purse_order:
            raise Exception("创建取现订单失败")
        pay_purse_order = new_weixin_pay_purse_order['obj']
        try:
            # 提交支付到零钱
            order_info, info = request_wx_pay(order_id, int(amount * 100), customer.openid)
            if order_info and info:
                if info['result_code'] == "SUCCESS":
                    pay_purse_order.original_amount = customer.purse
                    pay_purse_order.result_code = info['result_code']
                    pay_purse_order.payment_no = info['payment_no']
                    pay_purse_order.payment_time = info['payment_time']
                    customer.purse -= Decimal(amount)

                    if session_commit().get('code') == 'false':
                        raise Exception("订单数据提交失败，事务回滚")
                    return success_return(data=order_info, message="付款到用户零钱成功")
                # 调用统一创建订单接口失败
                else:
                    raise Exception(info['result_code'])
            elif order_info:
                pay_purse_order.original_amount = customer.purse
                pay_purse_order.result_code = info['result_code']
                err_code, err_code_des = order_info.split(':')
                pay_purse_order.err_code = err_code
                pay_purse_order.err_code_desc = err_code_des
                db.session.commit()
                raise Exception(order_info)
            else:
                raise Exception("请求无响应")
        except Exception as e:
            traceback.print_exc()
            return false_return(message=f"支付到零钱失败，{e}")
    except Exception as e:
        return false_return(message=str(e)), 400
