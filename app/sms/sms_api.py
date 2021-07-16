from flask_restplus import Resource, fields, reqparse

from .. import db, redis_db, default_api, logger
from ..swagger import return_dict
from .send_sms import send_verification_code

sms_ns = default_api.namespace('sms', path='/sms', description='短信API接口')

sms_add_parser = reqparse.RequestParser()
sms_add_parser.add_argument('phone', required=True, help='手机号码，国内号')
sms_add_parser.add_argument('stage', required=True, help='front | back')

return_json = sms_ns.model('ReturnRegister', return_dict)


@sms_ns.route('')
class SendSMS(Resource):
    @sms_ns.doc(body=sms_add_parser)
    @sms_ns.marshal_with(return_json)
    def post(self, **kwargs):
        """
        发送短信
        """
        args = sms_add_parser.parse_args()
        return send_verification_code(phone=args['phone'], stage=args['stage'])
