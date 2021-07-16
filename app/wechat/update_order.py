from app import db, logger
from app.models import ShopOrders, make_order_id, MemberPolicies, MemberRechargeRecords, make_uuid, Customers, \
    CUSTOMER_L1_CONSUMPTION, CUSTOMER_L2_CONSUMPTION
import datetime
from app.common import submit_return, session_commit
from app.public_method import new_data_obj, query_coupon, create_member_card_num
from app.rebates import calc_rebate
from app.rebate_calc import purchase_rebate
from decimal import Decimal


def update_order(data):
    logger.debug(f"{data} is ready to update order")
    if data:
        res = "success"
        trade_status = data['result_code']  # 业务结果  SUCCESS/FAIL
        out_trade_no = data['out_trade_no']  #
        new_wechat_pay = None
        # device_info 可以在支付的时候提交，在call_back的是否返回，此处用于辨识支付类型
        if data['device_info'] == "ShopOrder":
            """在线商城购买"""
            order = db.session.query(ShopOrders).with_for_update().filter(ShopOrders.id.__eq__(out_trade_no),
                                                                          ShopOrders.is_pay.__eq__(3),
                                                                          ShopOrders.status.__eq__(1),
                                                                          ShopOrders.delete_at.__eq__(None)).first()
            customer = order.consumer
            order_customer = customer.openid
        else:
            """会员充值"""
            order = db.session.query(MemberRechargeRecords).with_for_update().filter(
                MemberRechargeRecords.id.__eq__(out_trade_no),
                MemberRechargeRecords.is_pay.__eq__(3), MemberRechargeRecords.status.__eq__(1),
                MemberRechargeRecords.delete_at.__eq__(None)).first()
            customer = order.card.card_owner
            order_customer = order.card.card_owner.openid

            # 正常情况，在支付的时候就会创建支付关联记录，此处代码防止无记录，应该不会发生这种情况
            if not order.wechat_pay_result:
                new_wechat_pay = new_data_obj("WechatPay", **{"id": make_uuid(),
                                                              "openid": customer.openid,
                                                              "member_recharge_record_id": out_trade_no})
                if not new_wechat_pay or not new_wechat_pay['status']:
                    raise Exception(f"会员充值订单<{out_trade_no}>无关联支付记录，新建仍旧失败")

        if not order:
            raise Exception(f"订单 {out_trade_no} 不存在，或已完成支付")

        if trade_status == "SUCCESS":
            bank_type = data['bank_type']  # 付款银行
            cash_fee = int(data['cash_fee']) / 100  # 现金支付金额(分)
            pay_time = datetime.datetime.strptime(data['time_end'], "%Y%m%d%H%M%S")  # 支付完成时间
            total_fee = int(data['total_fee']) / 100  # 总金额(单位由分转元)
            trade_type = data['trade_type']  # 交易类型
            transaction_id = data['transaction_id']  # 微信支付订单号
            # seller_id = data['mch_id']  # 商户号
            consumer_openid = data['openid']  # 用户标识

            if consumer_openid != order_customer:
                raise Exception(f"回调中openid {consumer_openid}与订单记录不符{order_customer}")

            # 判断是否为首单
            if not customer.first_order_table or (
                    customer.first_order_table == 'ShopOrders' and not customer.first_order_id):
                # 为首单， 则将首单记录到用户信息中
                customer.first_order_table = data['device_info']
                customer.first_order_id = order.id

            # 2021-0509 这个if用于目前加盟商直营团购付款成功之后升级用户等级
            logger.debug("order lvl: " + str(order.upgrade_level) + "; c lvl: " + str(customer.level))
            logger.debug(str(customer))
            if order.upgrade_level and customer.level < order.upgrade_level:
                customer.level = order.upgrade_level
                customer.role_id = 2

            if data['device_info'] == 'MemberRecharge':
                wechat_pay_result = order.wechat_pay_result
                order.is_pay = 1
                wechat_pay_result.bank_type = bank_type
                wechat_pay_result.cash_fee = cash_fee
                wechat_pay_result.transaction_id = transaction_id
                wechat_pay_result.total_amount = total_fee
                wechat_pay_result.trade_type = trade_type
                wechat_pay_result.time_end = pay_time

                # 获取会员充值策略
                member_policies = MemberPolicies.query.filter_by(to_type=0, recharge_amount=total_fee).first()
                if not member_policies:
                    raise Exception(f"金额{total_fee}对应的充值策略未定义")

                # 获取订单对应用户会员卡数据
                now_card = order.card

                # 如果没有会员卡，则创建一张， 默认grade是1
                if not now_card:
                    card_no = create_member_card_num()
                    now_card = new_data_obj("MemberCards", **{"card_no": card_no, "customer_id": now_card.card_owner.id,
                                                              "open_date": datetime.datetime.now()})

                if now_card.member_type == 1:
                    # raise Exception("代理商不可充值，切不可降级会直客，如有特殊需求请联系客服")
                    logger.info("当前用户是代理商，目前允许充值")
                else:
                    # 如果是直客类型会员卡， 变更会员卡类型
                    now_card.member_type = member_policies.to_type

                    # 如果会员充值策略对应的级别大于当前级别，则升级会员级别，若小于等于则不变
                    if now_card.grade < member_policies.to_level:
                        now_card.grade = member_policies.to_level

                    # 会员余额变更，切增加赠送部分
                    if not now_card.balance:
                        now_card.balance = Decimal("0.00")

                    now_card.balance += Decimal(str(total_fee)) + Decimal(str(member_policies.present_amount))

                # 赠送部分也增加会员充值记录
                new_charge_record_present = new_data_obj("MemberRechargeRecords", **{"recharge_amount": total_fee,
                                                                                     "member_card": now_card.id,
                                                                                     "note": f"充值{total_fee}，依据策略{member_policies.id}, 赠送{member_policies.present_amount}",
                                                                                     "is_pay": 1})
                if not new_charge_record_present:
                    raise Exception(f"{order.id} 对应赠送金额记录生成失败")

                # 返佣计算
                calc_result = calc_rebate.calc(order.id, order.consumer, pay_type="MemberRecharge")
                if calc_result.get('code') != 'success':
                    res = calc_result.get('message')
                    logger.error(f"订单<{order.id}>返佣结果{res}")

                db.session.add(customer)
                session_commit()
            else:
                items = order.items_orders_id.all()
                if items:
                    # 更新订单数据
                    order.is_pay = 1
                    order.bank_type = bank_type
                    order.cash_fee = cash_fee
                    order.pay_time = pay_time
                    order.transaction_id = transaction_id
                    # 增加累积消费金额
                    customer.total_consumption += Decimal(str(cash_fee))

                    # 根据累计消费，提升用户等级。若退款降低总消费金额，同样会降低等级
                    if customer.level > 3:
                        pass
                    elif customer.total_consumption >= CUSTOMER_L2_CONSUMPTION:
                        customer.level = 3
                    elif CUSTOMER_L1_CONSUMPTION <= customer.total_consumption < CUSTOMER_L2_CONSUMPTION:
                        customer.level = 2
                    else:
                        customer.level = 1

                    # 商品订单处理
                    for item_order in items:
                        item_order.status = 1
                        item_order.customer_level = customer.level
                        if order.need_express == 1 and customer.bu_id:
                            new_verify = new_data_obj("ItemVerification",
                                                      **{"id": make_uuid(),
                                                         "item_order_id": item_order.id,
                                                         "verification_quantity": item_order.item_quantity,
                                                         "verification_customer_id": customer.id,
                                                         "bu_id": customer.bu_id
                                                         })
                            purchase_rebate(customer.id, new_verify['obj'].id)
                        else:
                            order.is_ship = 1
                            order.is_receipt = 1
                            logger.info('pickup in store')

                        # if item_order.special == 31:
                        #     # 封坛货物
                        #     standard_value = item_order.bought_sku.values
                        #     # 查找单位是‘斤’的数值
                        #     unit = ""
                        #     init_total = 0.00
                        #     for s in standard_value:
                        #         if s.standards.name == '斤':
                        #             init_total = s.value
                        #             unit = s.standards.name
                        #             break
                        #
                        #     for _ in range(0, item_order.item_quantity):
                        #         cargo_data = {"cargo_code": make_order_id('FT'), 'order_id': order.id,
                        #                       "storage_date": datetime.datetime.now(),
                        #                       "init_total": init_total,
                        #                       "last_total": init_total,
                        #                       "unit": unit,
                        #                       "owner_name": order.consumer.true_name,
                        #                       "owner_id": order.customer_id}
                        #         new_cargo = new_data_obj("TotalCargoes", **cargo_data)
                        #         if not new_cargo and not new_cargo.get('status'):
                        #             logger.error(f"{item_order.id}生成仓储记录失败，或者记录已存在")
                        #             res = f"{item_order.id}生成仓储记录失败，或者记录已存在"
                        # elif item_order.special == 32:
                        #     # 表示分装订单，此item为酒瓶
                        #     packing_order = order.packing_order.first()
                        #     packing_order.pay_at = pay_time
                        #     packing_order.parent_cargo.last_total -= packing_order.consumption

                    if res == 'success':
                        if session_commit().get("code") != 'success':
                            res = '数据提交失败'

                    # 返佣计算
                    # calc_result = calc_rebate.calc(order.id, order.consumer)
                    # if calc_result.get('code') != 'success':
                    #     res = calc_result.get('message')
                    #     logger.error(f"订单<{order.id}>返佣结果{res}")

                    if res == 'success':
                        if session_commit().get("code") != 'success':
                            logger.error(f"订单<{order.id}>返佣结果数据提交失败")
                            res = '数据提交失败'
                else:
                    res = '此订单无关联商品订单'
        else:
            res = "ERROR: pay failed! "
            order.is_pay = 2
            if data['device_info'] == 'MemberRecharge':
                order.wechat_pay_result.callback_err_code = data['err_code']
                order.wechat_pay_result.callback_err_code_desc = data['err_code_des']
            else:
                # 更新订单，把错误信息更新到订单中
                order.pay_err_code = data['err_code']  # 错误代码
                order.pay_err_code_des = data['err_code_des']  # 错误代码描述
            db.session.add(order)
            session_commit()
    else:
        res = "回调无内容"

    return res
