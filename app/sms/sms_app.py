from flask_restplus import Resource, reqparse
from ..models import SMSApp
from .. import db
from ..common import success_return, false_return, session_commit
from ..decorators import permission_required
from ..swagger import return_dict, head_parser, page_parser
from .sms_api import sms_ns
from ..public_method import new_data_obj, get_table_data

sms_app_add_parser = reqparse.RequestParser()
sms_app_add_parser.add_argument('app_id', required=True, help='短信平台APP ID')
sms_app_add_parser.add_argument('app_key', required=True, help='短信平台APP key')
sms_app_add_parser.add_argument('platform', help='短信接口平台，默认为tencent')
sms_app_add_parser.add_argument('callback_url', help='短信接口回调的URL')

sms_app_update_parser = sms_app_add_parser.copy()
sms_app_update_parser.replace_argument('app_id', required=False, help='短信平台APP ID')
sms_app_update_parser.replace_argument('app_key', required=False, help='短信平台APP key')

return_json = sms_ns.model('ReturnRegister', return_dict)


@sms_ns.route('/apps')
@sms_ns.expect(head_parser)
class SMSAppsAPI(Resource):
    @sms_ns.marshal_with(return_json)
    @sms_ns.doc(body=page_parser)
    @permission_required("app.sms.sms_app.query_apps")
    def get(self, **kwargs):
        """
        查询所有短息接口app信息
        """
        args = page_parser.parse_args()
        return success_return(data=get_table_data(SMSApp, args))

    @sms_ns.doc(body=sms_app_add_parser)
    @sms_ns.marshal_with(return_json)
    @permission_required("app.sms.sms_app.add_app")
    def post(self, **kwargs):
        """
        添加短信平台APP 信息
        """
        args = sms_app_add_parser.parse_args()
        new_template = new_data_obj('SMSApp', **{'app_id': args['app_id'], 'app_key': args['app_key']})
        if new_template['status']:
            new_template['obj'].name = args.get("app_key")
            new_template['obj'].content = args.get("callback_url")
            new_template['obj'].platform = args.get('platform') if args.get('platform') else 'tencent'
        else:
            return false_return(message="此APP ID已存在"), 400
        return success_return(data={"id": new_template['obj'].id, "app_id": new_template['obj'].app_id},
                              message="短信APP已添加") if session_commit() else false_return(message="短信APP添加失败"), 400


@sms_ns.route('/app/<int:id>')
@sms_ns.param('id', '数据库中的ID字段')
@sms_ns.expect(head_parser)
class SMSAppAPI(Resource):
    @sms_ns.doc(body=sms_app_update_parser)
    @sms_ns.marshal_with(return_json)
    @permission_required("app.sms.sms_template.update_template")
    def put(self, **kwargs):
        """
        修改短信APP信息
        """
        app_ = SMSApp.query.get(kwargs.get('id'))
        args = sms_app_update_parser.parse_args()
        if app_:
            if args.get('app_id'):
                app_.app_id = args.get('app_id')
            if args.get('app_key'):
                app_.name = args.get('app_key')
            if args.get('platform'):
                app_.platform = args.get('platform')
            if args.get('callback_url'):
                app_.content = args.get('callback_url')
            db.session.add(app_)
            return success_return(message="更新成功") if session_commit() else false_return(message='更新失败'), 400
        else:
            return false_return(message=f"<{kwargs.get('id')}>不存在"), 400