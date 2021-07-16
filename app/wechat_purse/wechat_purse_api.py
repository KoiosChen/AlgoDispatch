from flask_restplus import Resource, reqparse
from ..models import ShopOrders, Permission, ItemsOrders, Refund, make_uuid, WechatPurseTransfer, make_order_id
from .. import db, redis_db, default_api, logger
from app.wechat import mmpaymkttransfers
from ..decorators import permission_required
from ..swagger import return_dict, head_parser, page_parser
from app.common import success_return, false_return, submit_return
from app.public_method import get_table_data

purse_ns = default_api.namespace('wechat purse', path='/wechat_purse', description='用户钱包相关接口')

return_json = purse_ns.model('ReturnRegister', return_dict)

withdraw_get_orders_parser = page_parser.copy()
withdraw_get_orders_parser.add_argument('status', required=False, type=int, help='提现状态，0，失败，1 成功', location='args')

withdraw_parser = reqparse.RequestParser()
withdraw_parser.add_argument("order_id", required=False, type=str, help='当提交失败后，用户可查询提现订单再次提交，重复提交用相同ID')
withdraw_parser.add_argument("amount", required=True, type=str, help='提现金额。无论提现订单号是否提交，金额必须提交。若再次提交订单，金额必须和该订单的相同')


@purse_ns.route('/withdraw')
@purse_ns.expect(head_parser)
class WithDrawAPI(Resource):
    @purse_ns.doc(body=withdraw_get_orders_parser)
    @purse_ns.marshal_with(return_json)
    @permission_required(Permission.BU_WAITER)  # 当前仅支持BU提现
    def get(self, **kwargs):
        """提现接口查询"""
        args = withdraw_get_orders_parser.parse_args()
        args['search'] = dict()
        args['search']['customer_id'] = kwargs['current_user'].id
        return success_return(data=get_table_data(WechatPurseTransfer, args, order_by="payment_time"))

    @purse_ns.doc(body=withdraw_parser)
    @purse_ns.marshal_with(return_json)
    @permission_required(Permission.BU_WAITER)
    def post(self, **kwargs):
        """用户取现到零钱接口"""
        try:
            current_user = kwargs['current_user']
            args = withdraw_parser.parse_args()
            order_id = args.get('order_id')
            amount = args['amount']
            if order_id:
                withdraw_order = WechatPurseTransfer.query.get(order_id)
                assert withdraw_order, "订单不存在"
                assert withdraw_order.amount == amount, "订单金额和此次提交金额不符"
            else:
                order_id = make_order_id(prefix='PURSE')
            return mmpaymkttransfers.weixin_pay_purse(order_id=order_id, amount=eval(amount),
                                                      customer_id=current_user.id)

        except Exception as e:
            return false_return(message=str(e)), 400
