from . import logger, fdfs_client
from .common import false_return, success_return, session_commit
from .models import *
from sqlalchemy import and_
import datetime
import traceback
from decimal import Decimal
from app.pykube import KubeMgmt


def format_decimal(num, zero_format="0.00", to_str=False):
    print(type(num))
    if isinstance(num, float) or isinstance(num, int) or isinstance(num, str):
        return str(num)
    else:
        formatted_ = num.quantize(Decimal(zero_format))
        if to_str:
            return str(formatted_)
        else:
            return formatted_


def new_data_obj(table, **kwargs):
    """
    创建新的数据对象
    :param table: 表名
    :param kwargs: 表数据，需要对应表字段
    :return: 新增，或者已有数据的对象
    """
    logger.debug(f">>> Check the {table} for data {kwargs}")
    __obj = eval(table).query.filter_by(**kwargs).first()
    new_one = True
    if not __obj:
        logger.debug(f">>> The table {table} does not have the obj, create new one!")
        try:
            __obj = eval(table)(**kwargs)
            db.session.add(__obj)
            db.session.flush()
        except Exception as e:
            logger.error(f'create {table} fail {kwargs} {e}')
            traceback.print_exc()
            db.session.rollback()
            raise Exception(f"create new record in {table.__class__.__name__} failed for {e}")
    else:
        logger.debug(f">>> The line exist in {table} for {kwargs}")
        new_one = False
    return {'obj': __obj, 'new_one': new_one}


def table_fields(table, appends: list, removes: list):
    original_fields = getattr(getattr(table, '__table__'), 'columns').keys()
    for a in appends:
        original_fields.append(a)
    for r in removes:
        if r in original_fields:
            original_fields.remove(r)
    return original_fields


def find_id(elements_list):
    id_ = list()
    for el in elements_list:
        if el.get('children'):
            id_.extend(find_id(el['children']))
            id_.append(el['id'])
            return id_
        else:
            return [el['id']]


def _make_table(fields, table, strainer=None):
    tmp = dict()
    for f in fields:
        if f == 'roles':
            tmp[f] = [get_table_data_by_id(eval(role.__class__.__name__), role.id, ['elements']) for role in
                      table.roles]
        elif f == 'role':
            try:
                tmp[f] = {"id": table.role.id, "name": table.role.name}
            except Exception as e:
                logger.error(f"get role fail {e}")
                tmp[f] = {}
        elif f == 'children':
            if table.children:
                child_tmp = list()
                for child in table.children:
                    if strainer is not None:
                        if child.type == strainer[0] and child.id in strainer[1]:
                            child_tmp.extend(_make_data([child], fields, strainer))
                    else:
                        child_tmp.extend(_make_data([child], fields, strainer))
                tmp[f] = child_tmp
        elif f == 'objects':
            tmp1 = list()
            t1 = getattr(table, f)
            for value in t1:
                if value.thumbnails:
                    tmp1.append({'id': value.id, 'url': value.url, 'obj_type': value.obj_type,
                                 'thumbnail': {'id': value.thumbnails[0].id,
                                               'url': value.thumbnails[0].url,
                                               'obj_type': value.thumbnails[0].obj_type}})
                else:
                    tmp1.append({'id': value.id, 'url': value.url, 'obj_type': value.obj_type})
            tmp1.sort(key=lambda x: x["obj_type"], reverse=True)
            tmp[f] = tmp1
        elif f == 'values':
            tmp1 = list()
            t1 = getattr(table, f)
            for value in t1:
                tmp1.append({'value': value.value, 'standard_name': value.standards.name})
            tmp[f] = tmp1
        elif f == 'standards':
            if table.standards:
                tmp[f] = [{"id": e.id, "name": e.name} for e in table.standards]
            else:
                tmp[f] = []
        elif f == 'shop_order_verbose':
            if table.shop_order_id:
                table_name = table.related_order.__class__.__name__
                tmp[f] = get_table_data_by_id(eval(table_name), table.shop_order_id, appends=['real_payed_cash_fee'])
        elif f == 'config_files':
            if table.config_files:
                tmp[f] = get_table_data_by_id(eval(table.config_files.__class__.__name__), table.config_files.id)
        else:
            r = getattr(table, f)
            if isinstance(r, int) or isinstance(r, float):
                tmp[f] = r
            elif r is None:
                tmp[f] = ''
            else:
                tmp[f] = str(r)
    return tmp


def _make_data(data, fields, strainer=None):
    rr = list()
    for t in data:
        rr.append(_make_table(fields, t, strainer))
    return rr


def _search(table, fields, search):
    and_fields_list = list()
    for k, v in search.items():
        if k in fields:
            if k in ('delete_at', 'used_at') and v is None:
                and_fields_list.append(getattr(getattr(table, k), '__eq__')(v))
            elif k in ('manager_customer_id', 'owner_id') and v:
                and_fields_list.append(getattr(getattr(table, k), '__eq__')(v))
            elif k in ('validity_at', 'end_at') and v is not None:
                and_fields_list.append(getattr(getattr(table, k), '__ge__')(v))
            elif k == 'start_at' and v is not None:
                and_fields_list.append(getattr(getattr(table, k), '__le__')(v))
            elif k == 'pay_at' and v == 'not None':
                and_fields_list.append(getattr(getattr(table, k), '__ne__')(None))
            else:
                and_fields_list.append(getattr(getattr(table, k), 'contains')(v))
    return and_fields_list


def _advance_search(table, advance_search):
    and_fields_list = list()

    for search in advance_search:
        keys = search['key'].split('.')
        tmp_table = table
        for k in keys:
            if hasattr(tmp_table, k):
                tmp_table = getattr(tmp_table, k)
            else:
                logger.error(f"{tmp_table} has no attribute {k}")
        attr_key = tmp_table
        and_fields_list.append(getattr(attr_key, search['operator'])(search['value']))
    return and_fields_list


def get_table_data(table, args, appends=None, removes=None, advance_search=None, order_by=None):
    if appends is None:
        appends = []
    if removes is None:
        removes = []
    page = args.get('page')
    current = args.get('current')
    size = args.get('size')
    search = args.get('search')
    fields = table_fields(table, appends, removes)
    table_name = table.__name__
    if 'parent_id' in fields and table_name == 'Elements':
        base_sql = table.query.filter(table.parent_id.__eq__(None))
    else:
        base_sql = table.query

    if isinstance(current, int) and current <= 0:
        return False

    filter_args = list()
    if search:
        filter_args.extend(_search(table, fields, search))
        if advance_search is not None:
            filter_args.extend(_advance_search(table, advance_search))
        search_sql = base_sql.filter(and_(*filter_args))
    else:
        if advance_search is not None:
            filter_args.extend(_advance_search(table, advance_search))
            search_sql = base_sql.filter(and_(*filter_args))
        else:
            search_sql = base_sql

    if order_by is not None:
        search_sql = search_sql.order_by(getattr(getattr(table, order_by), "desc")())

    page_len = search_sql.count()
    if page != 'true':
        table_data = search_sql.all()
    else:
        if page_len < (current - 1) * size:
            current = 1
        table_data = search_sql.offset((current - 1) * size).limit(size).all()

    r = _make_data(table_data, fields)

    if table.__name__ == 'Elements':
        pop_list = list()
        for record in r:
            if record.get('parent_id'):
                pop_list.append(record)
        for p in pop_list:
            r.remove(p)

    return {"records": r, "total": page_len, "size": size, "current": current} if page == 'true' else {"records": r}


def get_table_data_by_id(table, key_id, appends=None, removes=None, strainer=None, search=None, advance_search=None):
    if removes is None:
        removes = []
    if appends is None:
        appends = []
    fields = table_fields(table, appends, removes)
    base_sql = table.query
    if search is None and advance_search is None:
        t = base_sql.get(key_id)
    elif advance_search is not None:
        filter_args = _advance_search(table, advance_search)
        filter_args.append(getattr(getattr(table, 'id'), '__eq__')(key_id))
        t = base_sql.filter(and_(*filter_args)).first()
    else:
        filter_args = _search(table, fields, search)
        filter_args.append(getattr(getattr(table, 'id'), '__eq__')(key_id))
        t = base_sql.filter(and_(*filter_args)).first()
    if t:
        return _make_table(fields, t, strainer)
    else:
        return {}


def create_member_card_num(prefix='777'):
    today = datetime.datetime.now()
    return prefix + str(today.year) + str(today.month).zfill(2) + str(today.day).zfill(2) + str(
        random.randint(1000, 9999))


def upload_fdfs(file):
    filename = file.filename
    extension = filename.split('.')[-1] if '.' in filename else ''
    ret = fdfs_client.upload_by_buffer(file.read(), file_ext_name=extension)
    logger.info(ret)
    fdfs_store_path = ret['Remote file_id'].decode()
    return fdfs_store_path


def run_job(job, order):
    """
    目前仅支持k8s运行job
    :param order:
    :param job:
    :return:
    """
    try:
        kube_job = KubeMgmt(job.run_env)
        kube_job.load_yaml(job.id)
        kube_job.cfg['metadata']['name'] = f"{order.name}-{order.run_times}"
        start_result = kube_job.start_job()
        if start_result.get('code') != 'success':
            raise Exception(start_result['message'])
        order.run_times += 1
        job_name = kube_job.cfg['metadata']['name']
        # kube_job.watch_job(job_name)
        start_result['data']['child_order_id'] = order.id
        return start_result
    except Exception as e:
        traceback.print_exc()
        return false_return(message=str(e))


def run_downstream(**kwargs):
    """

    :param kwargs: job_id 未当前任务的ID，即父级ID， 用来启动下游JOB
    :return:
    """
    try:
        job_id = kwargs['job_id']
        upstream_order_id = kwargs.get('upstream_order_id')
        force = kwargs.get('force')
        job = Jobs.query.get(job_id)
        if not job:
            raise Exception(f"{job_id} does not exist.")

        child_jobs = job.children

        if not child_jobs:
            return success_return(message='no children job')

        run_results = []
        for child_job in child_jobs:
            if child_job.run_env in ('k8sm01', 'k8sm02'):
                new_child_job_order = new_data_obj("Orders", **{"parent_id": upstream_order_id,
                                                                "job_id": child_job.id})

                if not new_child_job_order.get('new_one') and force == 0:
                    raise Exception('下游任务已执行')

                if not new_child_job_order['obj'].name:
                    new_child_job_order['obj'].name = f"{Orders.query.get(upstream_order_id).name}-{child_job.name}"

                run_results.append(run_job(child_job, new_child_job_order.get('obj')))
        failed_list = list()
        success_list = list()
        if run_results:
            for result in run_results:
                if result.get('code') != 'success':
                    failed_list.append(result.get('message'))
                else:
                    success_list.append(result.get('data'))

        if not failed_list:
            return success_return(message='run job success', data=success_list)
        else:
            return false_return(data=failed_list)
    except Exception as e:
        traceback.print_exc()
        return false_return(message=f"{e}")
