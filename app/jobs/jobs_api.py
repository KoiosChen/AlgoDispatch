from flask import request
from flask_restplus import Resource, reqparse
from ..models import Jobs
from . import jobs
from .. import db, default_api
from ..common import success_return, false_return, session_commit, submit_return
from werkzeug.datastructures import FileStorage
from ..public_method import table_fields, new_data_obj
from ..decorators import permission_required
from ..swagger import return_dict, head_parser, page_parser
from ..public_method import get_table_data, get_table_data_by_id, upload_fdfs

jobs_ns = default_api.namespace('jobs', path='/jobs',
                                description='任务的增删改查，任务的继承关系等')

register_parser = reqparse.RequestParser()
register_parser.add_argument('name', required=True, help='任务名称')
register_parser.add_argument('desc', help='任务描述')
register_parser.add_argument('run_env', help='运行环境，k8s，docker， docker-compose')
register_parser.add_argument('run_type', help='运行类型，job，crontab，once等')
register_parser.add_argument('input_params', help='启动job所需要的参数')
register_parser.add_argument('seq', help='同级任务执行顺序')
register_parser.add_argument('parent_id', help='父级job ID， 可通过job get方法获取ID')
register_parser.add_argument('master', help='指定K8S master')
# ?register_parser.add_argument('arguments', help='元数据，根据运行环境和运行类型不同，来定义相应的参数', location='json', type=dict)
register_parser.add_argument('file', required=True, type=FileStorage, location='files')
# register_parser.add_argument('Authorization', required=True, location='headers')

update_job_parser = register_parser.copy()
update_job_parser.replace_argument('name', required=False, help='任务名称')

return_json = jobs_ns.model('ReturnRegister', return_dict)

jobs_page_parser = page_parser.copy()
jobs_page_parser.add_argument('name', help='name', location='args')


@jobs_ns.route('')
class QueryJobs(Resource):
    @jobs_ns.marshal_with(return_json)
    @permission_required("app.jobs.jobs_api.get")
    @jobs_ns.expect(jobs_page_parser)
    def get(self):
        """
        获取所有job
        """
        args = jobs_page_parser.parse_args()
        args['search'] = dict()
        if args.get("name"):
            args['search']['name'] = args.get('name')
        return success_return(get_table_data(Jobs, args, removes=['creator_id', 'parent_id'], appends=['children']),
                              "请求成功")

    @jobs_ns.doc(body=register_parser)
    @jobs_ns.marshal_with(return_json)
    @permission_required("app.jobs.jobs_api.post")
    def post(self, **kwargs):
        """
        添加任务定义
        """
        run_env_validate = {"k8s": {"job": ["master"],
                                    "crontab": ["master"]},
                            "docker": ["docker_host"]}
        try:
            args = register_parser.parse_args()
            name = args.get('name')
            desc = args.get('desc')
            run_env = args.get('run_env')
            run_type = args.get('run_type')
            input_params = args.get('input_params')
            arguments = args.get('arguments')
            seq = args.get('seq')
            parent_id = args.get('parent_id')
            upload_object = args['file']
            args['filename'] = upload_object.filename
            # 当前没有用户认证的步骤，所以job name需要唯一
            new_job = new_data_obj("Jobs", **{"name": name})
            if not new_job.get('new_one'):
                raise Exception(f'Job name {name} exist.')

            the_job = new_job.get('obj')
            the_job.desc = desc
            the_job.run_env = run_env
            the_job.input_params = input_params
            the_job.seq = seq
            if parent_id and the_job.parent_id is None:
                parent_obj = Jobs.query.get(parent_id)
                parent_obj.children.append(the_job)
            if arguments:
                for key, value in arguments:
                    if key not in run_env_validate.get(run_env):
                        raise Exception(f"配置参数{key}和运行环境{run_env}不匹配, 当前运行环境允许参数{run_env_validate.get(run_env)}")
                    arg_name_obj = new_data_obj('ArgName', **{"name": key})
                    arg_name_id = arg_name_obj.get('obj').id
                    new_arguments = new_data_obj('Arguments', **{"arg_name_id": arg_name_id, "value": value})
                    the_job.arguments.append(new_arguments.get('obj'))

            if upload_object:
                print(args.get('filename'))
                file_store_path = upload_fdfs(upload_object)
                new_config_file = new_data_obj("ConfigFiles", **{"filename": upload_object.filename,
                                                                 "storage": file_store_path,
                                                                 "job_id": the_job.id})

            return submit_return('Successfully created job',
                                 'Failed to create job, db commit error',
                                 data={"id": the_job.id})
        except Exception as e:
            return false_return(message=f'create job failed for {e}')


@jobs_ns.route('/<string:job_id>')
@jobs_ns.expect(head_parser)
@jobs_ns.param("job_id", "定义的JOB ID, 通过/job的get方法查询")
class JobById(Resource):
    @jobs_ns.doc(body=update_job_parser)
    @jobs_ns.marshal_with(return_json)
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

    @jobs_ns.marshal_with(return_json)
    @permission_required("app.users.users_api.user_info")
    def get(self, **kwargs):
        """
        通过user id获取后端用户信息
        """
        return success_return(get_table_data_by_id(Users, kwargs['user_id'], ['roles'], ['password_hash']), "请求成功")
