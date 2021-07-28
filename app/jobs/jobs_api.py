from flask import request
from flask_restplus import Resource, reqparse
from ..models import Jobs
from . import jobs
from .. import db, default_api, logger
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
register_parser.add_argument('run_env', help='运行环境，选择K8S的Master， 目前支持k8sm01, k8sm02')
register_parser.add_argument('run_type', help='运行类型，job，cronjob等')
register_parser.add_argument('seq', help='同级任务执行顺序')
register_parser.add_argument('parent_id', help='父级job ID， 可通过job get方法获取ID')
register_parser.add_argument('master', help='指定K8S master')
# ?register_parser.add_argument('arguments', help='元数据，根据运行环境和运行类型不同，来定义相应的参数', location='json', type=dict)
register_parser.add_argument('file', required=True, type=FileStorage, location='files')
# register_parser.add_argument('Authorization', required=True, location='headers')

update_job_tags_parser = reqparse.RequestParser()
update_job_tags_parser.add_argument('tag', type=list, help='更新指定JOB的tag，若需要更新，需全量重传', location='json')

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
        return success_return(
            get_table_data(Jobs, args, removes=['creator_id', 'parent_id'], appends=['children', 'config_files']),
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
            seq = args.get('seq')
            parent_id = args.get('parent_id')
            upload_object = args.get('file')
            # 当前没有用户认证的步骤，所以job name需要唯一
            new_job = new_data_obj("Jobs", **{"name": name})
            if not new_job.get('new_one'):
                raise Exception(f'Job name {name} exist.')

            the_job = new_job.get('obj')
            the_job.desc = desc
            the_job.run_env = run_env
            the_job.seq = seq
            if parent_id and the_job.parent_id is None:
                parent_obj = Jobs.query.get(parent_id)
                parent_obj.children.append(the_job)
            # if arguments:
            #     for key, value in arguments:
            #         if key not in run_env_validate.get(run_env):
            #             raise Exception(f"配置参数{key}和运行环境{run_env}不匹配, 当前运行环境允许参数{run_env_validate.get(run_env)}")
            #         arg_name_obj = new_data_obj('ArgName', **{"name": key})
            #         arg_name_id = arg_name_obj.get('obj').id
            #         new_arguments = new_data_obj('Arguments', **{"arg_name_id": arg_name_id, "value": value})
            #         the_job.arguments.append(new_arguments.get('obj'))

            if upload_object:
                file_store_path = upload_fdfs(upload_object)
                new_config_file = new_data_obj("ConfigFiles", **{"filename": upload_object.filename,
                                                                 "storage": file_store_path,
                                                                 "job_id": the_job.id})

            return submit_return('Successfully created job',
                                 'Failed to create job, db commit error',
                                 data={"id": the_job.id})
        except Exception as e:
            return false_return(message=f'create job failed for {e}')


@jobs_ns.route('/<string:job_name>/tags')
@jobs_ns.param("job_name", "需要更新的job的name")
class JobByName(Resource):
    @jobs_ns.doc(body=update_job_tags_parser)
    @jobs_ns.marshal_with(return_json)
    @permission_required("app.jobs.jobs_api.job_by_name.put")
    def put(self, **kwargs):
        """
        修改任务自身标签，可作为参数传入order来执行K8S上的JOB
        """
        try:
            current_job = new_data_obj("Jobs", **{"name": kwargs['job_name']})
            if current_job.get('new_one'):
                raise Exception(f'Job name {kwargs["job_name"]} does not exist.')

            tags = update_job_tags_parser.parse_args()
            current_job['obj'].tags = []
            for tag in tags:
                tag_name = new_data_obj("ArgNames", **{'name': tag['name']}).get('obj')
                tag_map = new_data_obj("Arguments", **{'arg_name_id': tag_name.id, 'value': tag['value']})
                current_job['obj'].tags.append(tag_map)

            return submit_return(f'Successfully updated job, job_name={kwargs["job_name"]}',
                                 'Failed to update job, db commit error')

        except Exception as e:
            return false_return(message=f'update job failed, {e}'), 400

    @jobs_ns.marshal_with(return_json)
    @permission_required("app.jobs.jobs_api.job_by_name.get")
    def get(self, **kwargs):
        """
        通过user id获取后端用户信息
        """
        args = {'search': {'name': kwargs['job_name']}}
        return success_return(
            get_table_data(Jobs, args, removes=['creator_id', 'parent_id'], appends=['children', 'config_files']),
            "请求成功")
