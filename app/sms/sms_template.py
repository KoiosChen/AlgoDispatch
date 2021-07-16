from flask_restplus import Resource, reqparse
from ..models import SMSTemplate
from ..common import success_return, false_return, session_commit
from ..decorators import permission_required
from ..swagger import return_dict, head_parser, page_parser
from .sms_api import sms_ns
from ..public_method import new_data_obj, get_table_data

sms_template_add_parser = reqparse.RequestParser()
sms_template_add_parser.add_argument('template_id', required=True, help='短信平台模板ID')
sms_template_add_parser.add_argument('name', help='模板名称')
sms_template_add_parser.add_argument('content', help='模板内容，参数用{1} {2}表示')
sms_template_add_parser.add_argument('platform', help='指定此模板发送的接口')

sms_template_update_parser = sms_template_add_parser.copy()
sms_template_update_parser.replace_argument('template_id', required=False, help='短信平台模板ID')

return_json = sms_ns.model('ReturnRegister', return_dict)


@sms_ns.route('/templates')
@sms_ns.expect(head_parser)
class SMSTemplatesAPI(Resource):
    @sms_ns.marshal_with(return_json)
    @sms_ns.doc(body=page_parser)
    @permission_required("app.sms.sms_template.query_templates")
    def get(self, **kwargs):
        """
        查询所有短息模板
        """
        args = page_parser.parse_args()
        return success_return(data=get_table_data(SMSTemplate, args))

    @sms_ns.doc(body=sms_template_add_parser)
    @sms_ns.marshal_with(return_json)
    @permission_required("app.sms.sms_template.add_template")
    def post(self, **kwargs):
        """
        添加短信模板
        """
        args = sms_template_add_parser.parse_args()
        new_template = new_data_obj('SMSTemplate', **{'template_id': args['id']})
        if new_template['status']:
            new_template['obj'].name = args.get("name")
            new_template['obj'].content = args.get("content")
            new_template['obj'].platform = args.get('platform') if args.get('platform') else 'tencent'
        else:
            return false_return(message="此模板ID已存在"), 400
        return success_return(data={"id": new_template['obj'].id, "template_id": new_template['obj'].template_id},
                              message="短信模板已添加") if session_commit() else false_return(message="短信模板添加失败"), 400


@sms_ns.route('/templates/<int:id>')
@sms_ns.param('id', '数据库中的ID字段')
@sms_ns.expect(head_parser)
class SMSTemplateAPI(Resource):
    @sms_ns.doc(body=sms_template_update_parser)
    @sms_ns.marshal_with(return_json)
    @permission_required("app.sms.sms_template.update_template")
    def put(self, **kwargs):
        """
        修改短信模板
        """
        template_ = SMSTemplate.query.get(kwargs.get('id'))
        args = sms_template_update_parser.parse_args()
        if template_:
            if args.get('template_id'):
                template_.template_id = args.get('template_id')
            if args.get('name'):
                template_.name = args.get('name')
            if args.get('content'):
                template_.content = args.get('content')
            return success_return(message="更新成功")
        else:
            return false_return(message=f"<{kwargs.get('id')}>不存在"), 400