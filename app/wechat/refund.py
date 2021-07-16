# -*- coding: utf-8 -*-
from app import db
from app.models import Refund, CERT_PATH, KEY_PATH
import traceback
import requests
import json
from app.common import success_return, false_return, session_commit
from .public_method import *


def make_payment_info(notify_url=None, transaction_id=None, out_trade_no=None, out_refund_no=None, total_fee=None,
                      refund_fee=None):
    order_info = {'appid': app_id,
                  'mch_id': WEIXIN_MCH_ID,
                  'nonce_str': '',
                  'sign_type': WEIXIN_SIGN_TYPE,
                  'transaction_id': str(transaction_id),
                  'out_trade_no': str(out_trade_no),
                  'out_refund_no': str(out_refund_no),
                  'total_fee': total_fee,
                  'refund_fee': refund_fee,
                  'refund_fee_type': 'CNY',
                  'notify_url': notify_url}
    return order_info


def make_refund_request_wx(notify_url, transaction_id, out_trade_no, out_refund_no, total_fee, refund_fee):
    """
    微信统一下单，并返回客户端数据
    :param notify_url: 回调地址
    :param transaction_id: 微信订单号
    :param out_trade_no: 订单编号
    :param out_refund_no: 商户退款单号
    :param total_fee: 订单金额
    :param refund_fee: 退款金额
    :return: app所需结果数据
    """

    def make_payment_request(params_dict, unified_order_url):
        """
        生成返回给客户端APP的数据参数
        """
        data = generate_request_data(params_dict)
        headers = {'Content-Type': 'application/xml'}
        logger.debug(CERT_PATH + " " + KEY_PATH)
        req = requests.post(unified_order_url, data=data, headers=headers, cert=(CERT_PATH, KEY_PATH))
        if req.status_code == 200:
            result = json.loads(json.dumps(xmltodict.parse(req.content)))
            logger.debug(result)
            xml_content = result['xml']
            if xml_content['return_code'] == 'SUCCESS' and xml_content['result_code'] == 'SUCCESS':
                return result['xml']
            elif xml_content['return_code'] == 'SUCCESS':
                return result['xml']['err_code'] + ": " + result['xml']['err_code_des']
            else:
                return result['xml']['return_code'] + ': ' + result['xml']['return_msg']
        return None

    if float(total_fee) < 0.01:
        raise Exception('金额不能小于0.01')

    # 返回退货接口请求参数
    payment_info = make_payment_info(notify_url=notify_url,
                                     transaction_id=transaction_id,
                                     out_trade_no=out_trade_no,
                                     out_refund_no=out_refund_no,
                                     total_fee=total_fee,
                                     refund_fee=refund_fee)

    # 退货接口提交请求
    res = make_payment_request(payment_info, WEIXIN_REFUND_API)
    return res


def weixin_refund(order_refund_id):
    """
    【API】: 退货,供商户app调用
    """
    # order = ShopOrders.query.get(out_trade_no)
    refund_order = Refund.query.get(order_refund_id)
    i_order = refund_order.item_order
    order = i_order.shop_orders
    try:
        # 后台提交退货请求
        if not refund_order:
            raise Exception(f"退货订单 {order_refund_id} 不存在")
        if not i_order:
            raise Exception(f"无对应退货商品订单")
        if order.is_pay != 1:
            raise Exception(f"订单 {order.id} 未支付，不能退货")

        # 提交支付
        order_info = make_refund_request_wx(WEIXIN_REFUND_CALLBACK_API, order.transaction_id, order.id,
                                            refund_order.id,
                                            int(order.cash_fee * 100),
                                            int(i_order.transaction_price * i_order.item_quantity * 100))

        if order_info:
            if order_info['result_code'] == "SUCCESS":
                logger.info(f"商品<{i_order.id}>退货申请提交成功")
                i_order.status = 3
                i_order.refund_id = order_info['refund_id']
                i_order.refund_fee = order_info['refund_fee']
                i_order.cash_refund_fee = order_info['cash_refund_fee']
                db.session.add(i_order)
                if session_commit().get('code') == 'false':
                    raise Exception("订单数据提交失败，事务回滚")
                return success_return(data=order_info, message=f"退货订单<{order_refund_id}>，关于商品订单<{i_order.id}>退货申请成功")
            # 调用统一创建订单接口失败
            else:
                raise Exception(order_info['result_code'])
        elif order_info:
            raise Exception(order_info)
        else:
            raise Exception("请求无响应")
    except Exception as e:
        traceback.print_exc()
        if order and order.is_pay != 1:
            order.is_pay = 2
            db.session.add(order)
        session_commit()
        return false_return(message=f"支付失败，{e}")
