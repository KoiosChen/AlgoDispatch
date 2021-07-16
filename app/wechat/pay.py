# -*- coding: utf-8 -*-
from app import db, redis_db, sku_lock
from app.models import ShopOrders, Benefits, ShoppingCart, PackingItemOrders, Customers, MemberRechargeRecords, \
    make_uuid
from app.wechat.wechat_config import WEIXIN_SPBILL_CREATE_IP, WEIXIN_BODY, WEIXIN_UNIFIED_ORDER_URL, WEIXIN_CALLBACK_API
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


def make_payment_info(notify_url=None, out_trade_no=None, total_fee=None, openid=None, device_info=None):
    order_info = {'appid': app_id,
                  'mch_id': WEIXIN_MCH_ID,
                  'device_info': 'WEB',
                  'nonce_str': '',
                  'sign_type': WEIXIN_SIGN_TYPE,
                  'body': WEIXIN_BODY,
                  'out_trade_no': str(out_trade_no),
                  'total_fee': total_fee,
                  'spbill_create_ip': WEIXIN_SPBILL_CREATE_IP,
                  'notify_url': notify_url,
                  'trade_type': 'JSAPI',
                  'device_info': device_info,
                  'openid': openid}
    return order_info


def make_payment_request_wx(notify_url, out_trade_no, total_fee, openid, device_info):
    """
    微信统一下单，并返回客户端数据
    :param notify_url: 回调地址
    :param out_trade_no: 订单编号
    :param total_fee: 充值金额
    :return: app所需结果数据
    """

    def generate_call_app_data(params_dict, prepay_id):
        """
        将组合数据再次签名，客户端APP的数据参数包装
        """
        request_order_info = {
            'appId': params_dict['appid'],
            'nonceStr': generate_nonce_str(),
            'package': "prepay_id=" + prepay_id,
            'signType': 'MD5',
            'timeStamp': str(int(time.time()))
        }
        request_order_info['sign'] = generate_sign(request_order_info)
        return request_order_info

    def make_payment_request(params_dict, unified_order_url):
        """
        生成返回给客户端APP的数据参数
        """
        data = generate_request_data(params_dict)
        headers = {'Content-Type': 'application/xml'}
        req = requests.post(unified_order_url, data=data, headers=headers)
        if req.status_code == 200:
            result = json.loads(json.dumps(xmltodict.parse(req.content)))
            logger.debug(result)
            xml_content = result['xml']
            if xml_content['return_code'] == 'SUCCESS' and xml_content['result_code'] == 'SUCCESS':
                prepay_id = xml_content['prepay_id']
                # 将组合数据再次签名
                return generate_call_app_data(params_dict, prepay_id), result['xml']
            elif xml_content['return_code'] == 'SUCCESS':
                return result['xml']['err_code'] + ": " + result['xml']['err_code_des'], None
            else:
                return result['xml']['return_code'] + ': ' + result['xml']['return_msg'], None
        return None, None

    if float(total_fee) < 0.01:
        raise Exception('金额不能小于0.01')

    # 返回统一下单接口请求参数
    payment_info = make_payment_info(notify_url=notify_url,
                                     out_trade_no=out_trade_no,
                                     total_fee=total_fee,
                                     openid=openid,
                                     device_info=device_info)

    # 统一下单接口提交请求
    res, info = make_payment_request(payment_info, WEIXIN_UNIFIED_ORDER_URL)
    return res, info


def create_order(**kwargs):
    """
    用于生成订单，此时还未支付
    :param kwargs:
    :return:
    """

    try:
        upgrade_level = 0
        order_info = kwargs.get('order_info')
        packing_order = kwargs.pop('packing_order')
        packing_obj = None
        if packing_order:
            packing_obj = PackingItemOrders.query.get(packing_order)
        else:
            order_info.pop('packing_order')

        if not order_info.get('score_used'):
            order_info.pop('score_used')

        new_order = new_data_obj("ShopOrders", **order_info)
        if not new_order:
            raise Exception("订单创建失败，订单号创建失败")
        if not new_order['status']:
            return success_return(data=new_order['obj'].id, message='订单已存在')

        if packing_obj:
            # packing_obj.shop_order_id = new_order['obj'].id
            packing_obj.packing_item_order = new_order['obj']

        for item in kwargs.get('select_items'):
            item_obj = ShoppingCart.query.get(item)
            if not item_obj:
                raise Exception(f"购物车中{item}不存在")
            sku = item_obj.desire_sku
            if not sku or not sku.status or sku.delete_at:
                raise Exception(f"购物车对应商品不存在")

            item_price = sku.show_price if sku.show_price else sku.price
            customer = Customers.query.get(order_info['customer_id'])
            transaction_price = calc_sku_price(customer, sku, item)

            item_order = {"order_id": new_order['obj'].id, "item_id": sku.id,
                          "item_quantity": item_obj.quantity,
                          "item_price": item_price, "special": sku.special,
                          "customer_id": order_info.get('customer_id'),
                          "transaction_price": transaction_price}
            if item_obj.salesman_id:
                item_order['salesman_id'] = item_obj.salesman_id
            new_item_order = new_data_obj("ItemsOrders", **item_order)

            if new_item_order and new_item_order.get('status'):
                # 此处调用修改sku数量方法，数量传递为负数，因为这里一定是减少
                change_result = compute_quantity(sku, -item_obj.quantity)

                # 如果change_result是false， 那么表明出货失败
                if change_result.get("code") == "false":
                    raise Exception(json.dumps(change_result))

                # 如果这个sku有相关的促销活动，则记录
                if item_obj.combo:
                    new_item_order['obj'].benefits.append(Benefits.query.get(item_obj.combo))
                if item_obj.fgp_id and item_obj.fgp.upgrade_level > 0 and item_obj.fgp.upgrade_level > upgrade_level:
                    upgrade_level = item_obj.fgp.upgrade_level
            else:
                raise Exception("订单创建失败")
        if session_commit().get("code") == 'false':
            raise Exception("订单创建失败，因为事务提交失败")
        else:
            if upgrade_level > 0:
                new_order['obj'].upgrade_level = upgrade_level
                db.session.add(new_order['obj'])
                db.session.commit()
            for i in kwargs['select_items']:
                cart = ShoppingCart.query.get(i)
                cart.delete_at = datetime.datetime.now()
                db.session.add(cart)
            db.session.commit()
            return success_return(data=new_order['obj'].id, message="创建订单成功")

    except Exception as e:
        return false_return(str(e))


def weixin_pay(out_trade_no, price, openid, device_info="ShopOrder"):
    """
    【API】: 创建订单,供商户app调用
    """
    # order = ShopOrders.query.get(out_trade_no)
    customer = Customers.query.filter_by(openid=openid).first()
    if device_info == 'ShopOrder':
        order = db.session.query(ShopOrders).with_for_update().filter(ShopOrders.id.__eq__(out_trade_no),
                                                                      ShopOrders.customer_id.__eq__(customer.id),
                                                                      ShopOrders.status.__eq__(1)).first()
    else:
        order = db.session.query(MemberRechargeRecords).with_for_update().filter(
            MemberRechargeRecords.id.__eq__(out_trade_no)).first()

    try:
        # 后台提交支付请求
        if not order:
            raise Exception(f"订单 {out_trade_no} 不存在")
        if order.is_pay == 1 and order.pay_time:
            raise Exception(f"订单 {out_trade_no} 已支付")
        # if order.is_pay == 3 and not order.pay_time:
        #     raise Exception(f"订单 {out_trade_no} 支付中")

        # 先把订单状态更新为支付中
        order.is_pay = 3
        if session_commit().get("code") == "false":
            raise Exception("订单状态修改为‘支付中’失败")

        # 提交支付
        order_info, info = make_payment_request_wx(WEIXIN_CALLBACK_API, out_trade_no, int(price * 100), openid,
                                                   device_info)

        if order_info and info:
            info['total_amount'] = int(price * 100)
            if info['result_code'] == "SUCCESS":
                # 在返回小程序的package中增加订单号
                order_info['out_trade_no'] = out_trade_no
                order.is_pay = 3
                order.pre_pay_time = datetime.datetime.now()
                if info['device_info'] == "MemberRecharge":
                    # 如果是购物车中直接消费，那么正常情况没有微信支付记录
                    # 如果是订单中再付费，那么正常情况应该已经有微信支付记录
                    if not order.wechat_pay_result:
                        # 创建微信支付记录
                        new_wechat_pay = new_data_obj("WechatPay", **{"id": make_uuid(),
                                                                      "openid": customer.openid,
                                                                      "member_recharge_record_id": out_trade_no})
                        if not new_wechat_pay or not new_wechat_pay['status']:
                            raise Exception("创建支付关联记录失败")

                        new_wechat_pay['obj'].prepay_id = info['prepay_id']
                        new_wechat_pay['obj'].prepay_at = datetime.datetime.now()
                        new_wechat_pay['obj'].device_info = info['device_info']

                db.session.add(order)
                if session_commit().get('code') == 'false':
                    raise Exception("订单数据提交失败，事务回滚")
                return success_return(data=order_info, message="订单预付id获取成功")
            # 调用统一创建订单接口失败
            else:
                raise Exception(info['result_code'])
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
