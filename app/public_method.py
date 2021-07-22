import json
import random
import threading
import uuid
from . import logger, db, redis_db, fdfs_client
from .common import false_return, submit_return, success_return, session_commit
from .models import *
from sqlalchemy import and_
import datetime
import traceback
from flask import session
from decimal import Decimal
from app.pykube import KubeMaster


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


def table_fields(table, appends=[], removes=[]):
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
        elif f == 'classifies':
            tmp[f] = get_table_data_by_id(Classifies, table.classifies.id)
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


def get_table_data(table, args, appends=[], removes=[], advance_search=None, order_by=None):
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


def get_table_data_by_id(table, key_id, appends=[], removes=[], strainer=None, search=None, advance_search=None):
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


def create_member_card_by_invitation(current_user, invitation_code):
    member_card = current_user.member_card.first()

    # 此处目前仅支持邀请代理商
    if member_card and int(member_card.member_type) >= int(invitation_code.tobe_type) and int(
            member_card.grade) <= int(invitation_code.tobe_level):
        return false_return(message="当前用户已经是此级别(或更高级别），不可使用此邀请码"), 400

    if not member_card:
        card_no = create_member_card_num()
        new_member_card = new_data_obj("MemberCards", **{"card_no": card_no, "customer_id": current_user.id,
                                                         "open_date": datetime.datetime.now()})
    else:
        card_no = member_card.card_no
        new_member_card = {'obj': member_card, 'status': False}

    a = {"member_type": invitation_code.tobe_type,
         "grade": invitation_code.tobe_level,
         "validate_date": datetime.datetime.now() + datetime.timedelta(days=365)}

    for k, v in a.items():
        setattr(new_member_card['obj'], k, v)

    if new_member_card:
        if hasattr(invitation_code, "used_customer_id"):
            invitation_code.used_customer_id = current_user.id
        if hasattr(invitation_code, "new_member_card_id"):
            invitation_code.new_member_card_id = new_member_card['obj'].id
        if hasattr(invitation_code, "used_at"):
            invitation_code.used_at = datetime.datetime.now()
        if hasattr(invitation_code, "invitees"):
            invitation_code.invitees.append(new_member_card['obj'])

        current_user.invitor_id = invitation_code.manager_customer_id
        current_user.interest_id = invitation_code.interest_customer_id
        current_user.role_id = 2
        db.session.add(invitation_code)
        db.session.add(current_user)
    else:
        return false_return(message="邀请码有效，但是新增会员卡失败"), 400

    return submit_return(f"新增会员卡成功，卡号{card_no}, 会员级别{invitation_code.tobe_type} {invitation_code.tobe_level}",
                         "新增会员卡失败")


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


def run_job(job):
    """
    目前仅支持k8s运行job
    :param job:
    :return:
    """
    kube_job = KubeMaster(job.run_env, namespace='hmd')
    return kube_job.start_job(job_id=job.id)


def run_downstream(**kwargs):
    """

    :param kwargs: job_id 未当前任务的ID，即父级ID， 用来启动下游JOB
    :return:
    """
    try:
        job_id = kwargs['job_id']
        job = Jobs.query.get(job_id)
        if not job:
            raise Exception(f"{job_id} does not exist.")

        child_jobs = job.children

        if not child_jobs:
            return success_return(message='no children job')

        run_result = []
        for child_job in child_jobs:
            run_result.append(run_job(child_job))

        return success_return(data=run_result)
    except Exception as e:
        return false_return(message=f"{e}")