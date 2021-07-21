from flask import request
from flask_restplus import Resource, reqparse
from ..models import Orders
from . import orders
from .. import db, default_api
from ..common import success_return, false_return, session_commit, submit_return
from ..public_method import table_fields, new_data_obj
from ..decorators import permission_required
from ..swagger import return_dict, head_parser, page_parser
from ..public_method import get_table_data, get_table_data_by_id, upload_fdfs

orders_ns = default_api.namespace('orders', path='/orders', description='任务执行的记录，包括其状态等')

register_parser = reqparse.RequestParser()
register_parser.add_argument('name', required=True, help='任务名称')
register_parser.add_argument('desc', help='任务描述')
register_parser.add_argument('upstream_id', help='上游任务ID')
register_parser.add_argument('job_id', help='当前执行任务对应的任务定义ID')
register_parser.add_argument('status', help='状态，不传默认是1，正在运行，0：失败，1：正在运行，2：完成')
register_parser.add_argument('output', help='输出，作为下游任务的输入')

update_job_parser = register_parser.copy()
update_job_parser.replace_argument('name', required=False, help='任务名称')

return_json = orders_ns.model('ReturnRegister', return_dict)

orders_page_parser = page_parser.copy()
orders_page_parser.add_argument('name', help='name', location='args')


@orders_ns.route('')
class QueryOrders(Resource):
    @orders_ns.marshal_with(return_json)
    @permission_required("app.orders.orders_api.get")
    @orders_ns.expect(orders_page_parser)
    def get(self):
        """
        获取所有任务执行的订单
        """
        args = orders_page_parser.parse_args()
        args['search'] = dict()
        if args.get("name"):
            args['search']['name'] = args.get('name')
        return success_return(get_table_data(Orders, args, removes=['job_id']), "请求成功")

    @orders_ns.doc(body=register_parser)
    @orders_ns.marshal_with(return_json)
    @permission_required("app.jobs.jobs_api.post")
    def post(self, **kwargs):
        """
        添加任务执行订单
        """
        try:
            args = register_parser.parse_args()
            name = args.get('name')
            desc = args.get('desc')
            upstream_id = args.get('upstream_id')
            job_id = args.get('job_id')
            status = args.get('status')
            output = args.get('output')
            # name要求唯一
            new_order = new_data_obj("Orders", **{"name": name})
            if not new_order.get('new_one'):
                raise Exception(f'Order name {name} exist.')

            the_order = new_order.get('obj')
            the_order.desc = desc
            the_order.upstream_id = upstream_id
            the_order.job_id = job_id
            the_order.status = status
            if status == 2:
                # 如果是2，表示complete，查找下游任务并开始
                pass

            return submit_return('Successfully created job',
                                 'Failed to create job, db commit error',
                                 data={"id": the_order.id})
        except Exception as e:
            return false_return(message=f'create job failed for {e}')


@orders_ns.route('/<string:job_id>')
@orders_ns.expect(head_parser)
@orders_ns.param("job_id", "定义的JOB ID, 通过/job的get方法查询")
class JobById(Resource):
    @orders_ns.doc(body=update_job_parser)
    @orders_ns.marshal_with(return_json)
    @permission_required("app.jobs.jobs_api.job_by_id.put")
    def put(self, **kwargs):
        """
        修改任务定义
        """
        args = update_job_parser.parse_args()
        user = Jobs.query.get(kwargs['job_id'])
        if user:
            fields_ = table_fields(Jobs, appends=['role_id', 'password'], removes=['password_hash'])
            return modify_user_profile(args, user, fields_)
        else:
            return false_return(message="用户不存在"), 400

    @orders_ns.marshal_with(return_json)
    @permission_required("app.users.users_api.user_info")
    def get(self, **kwargs):
        """
        通过user id获取后端用户信息
        """
        return success_return(get_table_data_by_id(Users, kwargs['user_id'], ['roles'], ['password_hash']), "请求成功")
