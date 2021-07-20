from flask import request
from flask_restplus import Resource, reqparse
from ..models import Jobs
from . import jobs
from app.auth import auths
from .. import db, default_api
from ..common import success_return, false_return, session_commit, submit_return
from ..public_method import table_fields, new_data_obj
from ..public_user_func import create_user, modify_user_profile
from ..decorators import permission_required
from ..swagger import return_dict, head_parser, page_parser
from ..public_method import get_table_data, get_table_data_by_id

jobs_ns = default_api.namespace('jobs', path='/jobs',
                                description='任务的增删改查，任务的继承关系等')

register_parser = reqparse.RequestParser()
register_parser.add_argument('name', required=True, help='任务名称')
register_parser.add_argument('desc', help='任务描述')
register_parser.add_argument('run_env', help='运行环境，k8s，docker， docker-compose')
register_parser.add_argument('run_type', help='运行类型，job，crontab，once等')
register_parser.add_argument('input_params', help='启动job所需要的参数')
register_parser.add_argument('metadata', help='元数据，根据运行环境和运行类型不同，来定义相应的参数', location='json', type=dict)
# register_parser.add_argument('Authorization', required=True, location='headers')


return_json = jobs_ns.model('ReturnRegister', return_dict)

user_page_parser = page_parser.copy()
user_page_parser.add_argument('Authorization', required=True, location='headers')
user_page_parser.add_argument('phone', help='搜索phone字段', location='args')


@jobs_ns.route('')
class QueryJobs(Resource):
    @jobs_ns.marshal_with(return_json)
    @permission_required("app.jobs.jobs_api.get")
    @jobs_ns.expect(user_page_parser)
    def get(self, info):
        """
        获取所有job
        """
        args = page_parser.parse_args()
        args['search'] = dict()
        if args.get("creator"):
            args['search']['creator'] = args.get('creator')
        return success_return(get_table_data(Jobs, args, removes=['creator_id', 'parent_id'], appends=['children']),
                              "请求成功")

    @jobs_ns.doc(body=register_parser)
    @jobs_ns.marshal_with(return_json)
    @permission_required("app.jobs.jobs_api.post")
    def post(self, **kwargs):
        """
        添加任务定义
        """
        try:
            args = register_parser.parse_args()
            name = args.get('name')
            desc = args.get('desc')
            run_env = args.get('run_env')
            run_type = args.get('run_type')
            input_params = args.get('input_params')
            metadata = args.get('metadata')
            # 当前没有用户认证的步骤，所以job name需要唯一
            new_job = new_data_obj(Jobs, **{"name": name})
            if not new_job.get('status'):
                raise Exception(f'Job name {name} exist.')
            return create_user("Users", **args)
        except Exception as e:
            return false_return(message=f'create job failed for {e}')

    @jobs_ns.doc(body=update_user_parser)
    @jobs_ns.marshal_with(return_json)
    @permission_required("app.users.users_api.modify_self_attributes")
    def put(self, **kwargs):
        """
        修改登陆用户自己的属性
        """
        args = update_user_parser.parse_args()
        user = kwargs['info']['user']
        fields_ = table_fields(Users, appends=['role_id', 'password'], removes=['password_hash'])
        return modify_user_profile(args, user, fields_)


@jobs_ns.route('/login')
class Login(Resource):
    @jobs_ns.doc(body=login_parser)
    @jobs_ns.marshal_with(return_json)
    def post(self):
        """
        用户登陆，获取JWT
        """
        args = login_parser.parse_args()
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        username = args['username']
        password = args['password']
        method = args['method']
        platform = args['platform']
        return auths.authenticate(username, password, user_ip, platform, method=method)


@jobs_ns.route('/logout')
class Logout(Resource):
    @jobs_ns.marshal_with(return_json)
    @permission_required("app.users.users_api.logout")
    @jobs_ns.expect(head_parser)
    def post(self, info):
        """
        用户登出
        """
        login_info = info.get('login_info')
        db.session.delete(login_info)
        result = success_return(message="登出成功") if session_commit().get("code") == 'success' else false_return(
            message='登出失败'), 400
        return result


@jobs_ns.route('/<string:user_id>')
@jobs_ns.expect(head_parser)
@jobs_ns.param("user_id", "后台用户ID")
class UserById(Resource):
    @jobs_ns.doc(body=update_user_parser)
    @jobs_ns.marshal_with(return_json)
    @permission_required("app.users.users_api.modify_user_attributes")
    def put(self, **kwargs):
        """
        修改用户属性
        """
        args = update_user_parser.parse_args()
        user = Users.query.get(kwargs['user_id'])
        if user:
            fields_ = table_fields(Users, appends=['role_id', 'password'], removes=['password_hash'])
            return modify_user_profile(args, user, fields_)
        else:
            return false_return(message="用户不存在"), 400

    @jobs_ns.marshal_with(return_json)
    @permission_required("app.users.users_api.user_info")
    def get(self, **kwargs):
        """
        通过user id获取后端用户信息
        """
        return success_return(get_table_data_by_id(Users, kwargs['user_id'], ['roles'], ['password_hash']), "请求成功")


@jobs_ns.route('/<string:user_id>/password')
@jobs_ns.expect(head_parser)
@jobs_ns.param("user_id", "后台用户ID")
class ChangePassword(Resource):
    @jobs_ns.doc(body=pwd_parser)
    @jobs_ns.marshal_with(return_json)
    @permission_required("app.users.users_api.modify_user_attributes")
    def put(self, **kwargs):
        """
        修改用户密码
        """
        args = pwd_parser.parse_args()
        user = Users.query.get(kwargs['user_id'])
        if user and user.verify_password(args.get('old_password')):
            user.password = args.get('new_password')
            return submit_return("密码修改成功", "密码修改失败")
        else:
            return false_return(message="旧密码错误"), 400


@jobs_ns.route('/<string:user_id>/roles')
@jobs_ns.expect(head_parser)
@jobs_ns.param("user_id", "后台用户ID")
class UserRole(Resource):
    @permission_required("app.users.users_api.bind_role")
    @jobs_ns.doc(body=bind_role_parser)
    @jobs_ns.marshal_with(return_json)
    def post(self, **kwargs):
        """
        指定用户添加角色
        """
        args = bind_role_parser.parse_args()
        user = Users.query.get(kwargs.get('user_id'))
        if not user:
            return false_return(message='用户不存在'), 400
        old_roles = [r.id for r in user.roles]
        roles = args['role_id']
        to_add_roles = set(roles) - set(old_roles)
        to_delete_roles = set(old_roles) - set(roles)

        for roleid in to_add_roles:
            role_ = Roles.query.get(roleid)
            if not role_:
                return false_return(message=f'{roleid} is not exist'), 400
            if role_ not in user.roles:
                user.roles.append(role_)

        for roleid in to_delete_roles:
            role_ = Roles.query.get(roleid)
            if not role_:
                return false_return(message=f'{roleid} is not exist'), 400
            if role_ in user.roles:
                user.roles.remove(role_)

        return success_return(message='修改角色成功')
