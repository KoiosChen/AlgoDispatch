from flask import jsonify, request
from flask_restplus import Resource, fields, reqparse
from ..models import SMSApp
from . import sms
from app.auth import auths
from .. import db, redis_db, default_api, logger
from ..common import success_return, false_return, session_commit
import datetime
from ..decorators import permission_required
from ..swagger import return_dict, head_parser
from .sms_api import sms_ns
from ..public_method import new_data_obj, get_table_data

verify_code_parser = reqparse.RequestParser()
verify_code_parser.add_argument('code', required=True, help='短信验证码', location='json')
verify_code_parser.add_argument('stage', required=True, help='前端、后端， 可传递front | back | bu_employee', location='json')

return_json = sms_ns.model('ReturnRegister', return_dict)


@sms_ns.route('/<string:phone>/verify_code')
@sms_ns.param("phone", "用户手机号")
class VerifyCode(Resource):
    @sms_ns.doc(body=verify_code_parser)
    @sms_ns.marshal_with(return_json)
    def post(self, **kwargs):
        """
        核对手机验证码，仅用于验证手机号，登陆需要使用login接口
        """
        args = verify_code_parser.parse_args()
        key = args['stage'] + "::verification_code::" + kwargs['phone']
        if redis_db.exists(key) and redis_db.get(key) == args['code']:
            return success_return(message="验证码正确")
        else:
            return false_return(message="手机不存在或者验证码错误"), 403
