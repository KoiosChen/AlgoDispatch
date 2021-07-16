import jwt
import datetime
import time
from ..models import NewCustomerAwards, LoginInfo, Customers, SceneInvitation, NEW_ONE_SCORES, SHARE_AWARD, make_uuid, \
    Franchisees, CustomerRoles, FranchiseeOperators, BusinessUnitEmployees, SKU, FranchiseeGroupPurchase
from .. import db, logger, SECRET_KEY, redis_db
from ..common import success_return, false_return, session_commit, submit_return
from ..public_method import new_data_obj, create_member_card_by_invitation, get_table_data_by_id, query_coupon
import json
import traceback


def encode_auth_token(user_id, login_time, login_ip, platform):
    """
    生成认证Token
    “exp”: 过期时间
    “nbf”: 表示当前时间在nbf里的时间之前，则Token不被接受
    “iss”: token签发者
    “aud”: 接收者
    “iat”: 发行时间
    :param user_id: string
    :param login_time: int(timestamp)
    :param login_ip: string
    :return: string
    """
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=0, seconds=86400),
            'iat': datetime.datetime.utcnow(),
            'iss': 'infinicalc.com',
            'data': {
                'id': user_id,
                'login_time': login_time,
                'login_ip': login_ip,
                'platform': platform
            }
        }
        return jwt.encode(
            payload,
            SECRET_KEY,
            algorithm='HS256'
        )
    except Exception as e:
        logger.error(str(e))
        return false_return(message=str(e))


def authenticate(login_ip, **kwargs):
    """
    前端用户登录，目前只针对微信小程序环境
    :param kwargs: code2session接口返回的json
    :param login_ip: 用户发起请求的IP
    :return: json
    """
    try:
        open_id = kwargs['openid']
        session_key = kwargs['session_key']
        new_customer = new_data_obj("Customers", **{"openid": open_id, "delete_at": None, "status": 1})
        logger.debug(f"{new_customer}")
        if new_customer:
            session_commit()
        else:
            raise Exception(f"创建用户{open_id}失败")
        customer = new_customer['obj']

        logger.debug(f"{customer.business_unit_employee}, {customer.franchisee_operator}")

        # 如果数据是新建，那么表示新进入用户
        if new_customer['status']:
            # 如果是新用户，则可获取首单优惠券
            try:
                award_coupons = NewCustomerAwards.query.first().could_get_coupons
                for award_coupon in award_coupons:
                    query_result = query_coupon(current_user=customer, coupon_id=award_coupon.id)
                    logger.info(query_result)
            except Exception as e:
                traceback.print_exc()
                logger.error(str(e))

            # 若是新用户，则可获取新注册积分
            new_customer['obj'].total_points = NEW_ONE_SCORES
            new_data_obj("Scores", **{"id": make_uuid(),
                                      "customer_id": new_customer['obj'].id,
                                      "reason": f"login from {kwargs.get('shared_id')}",
                                      "quantity": NEW_ONE_SCORES})

        # 如果父级id为空，那么将此次父级id作为自己的父级
        logger.debug(f">>> shared id is {kwargs.get('shared_id')}")
        logger.debug(f">>> scene invitation is {kwargs.get('scene_invitation')}, scene is {kwargs.get('scene')}")

        if kwargs.get('scene_invitation') and not kwargs.get('scene'):
            # 如果有邀请码，调用邀请码模块
            si_obj = db.session.query(SceneInvitation).with_for_update().filter(
                SceneInvitation.code.__eq__(kwargs.get('scene_invitation'))).first()
            if si_obj and si_obj.start_at <= datetime.datetime.now() <= si_obj.end_at:
                now_invitees = len(si_obj.invitees)
                if si_obj.max_invitees == 0 or now_invitees < si_obj.max_invitees:
                    create_member_card_by_invitation(new_customer['obj'], si_obj)
        elif kwargs.get('scene_invitation') and kwargs.get('scene') and (
                not customer.business_unit_employee and not customer.franchisee_operator) and kwargs.get(
            'scene') != 'new_fgp':
            logger.debug(">>> scene invitation action")
            scene = kwargs.get('scene')
            scene_invitation = kwargs.get('scene_invitation')
            if scene in ('new_franchisee', 'new_bu', 'new_franchisee_employee', 'new_bu_employee'):
                logger.debug(f"scene is {scene}")
                if redis_db.exists(scene_invitation):
                    obj_id = redis_db.get(scene_invitation)
                    logger.debug(f"scene invitation mapped to value {obj_id}")
                    redis_db.delete(scene_invitation)
                    if scene == 'new_franchisee':
                        # bind to the franchisee
                        # 创建manager
                        job_role = CustomerRoles.query.filter_by(name="FRANCHISEE_MANAGER").first()
                        new_employee = new_data_obj("FranchiseeOperators", **{"customer_id": customer.id,
                                                                              "name": "老板（本人）",
                                                                              "job_desc": job_role.id,
                                                                              "franchisee_id": obj_id})
                        if not new_employee or (new_employee and not new_employee['status']):
                            logger.error("绑定加盟商失败")
                    elif scene == 'new_bu':
                        # bind to the bu
                        job_role = CustomerRoles.query.filter_by(name="BU_MANAGER").first()
                        new_employee = new_data_obj("BusinessUnitEmployees", **{"customer_id": customer.id,
                                                                                "name": "老板（本人）",
                                                                                "job_desc": job_role.id,
                                                                                "business_unit_id": obj_id})
                        if not new_employee or (new_employee and not new_employee['status']):
                            logger.error("绑定店铺失败")
                    elif scene == 'new_franchisee_employee':
                        # bind to the franchisee employee role
                        bind_f_e = FranchiseeOperators.query.get(obj_id)
                        bind_f_e.customer_id = customer.id
                        db.session.add(bind_f_e)
                    elif scene == 'new_bu_employee':
                        # bind to the bu employee role
                        bind_u_e = BusinessUnitEmployees.query.get(obj_id)
                        bind_u_e.customer_id = customer.id
                        db.session.add(bind_u_e)
                else:
                    logger.error('invitation code error')
            elif scene in ("new_customer", "new_member"):
                if redis_db.exists(scene_invitation):
                    obj_id = redis_db.get(scene_invitation)
                    redis_db.delete(scene_invitation)
                    bu_customer_obj = Customers.query.get(obj_id)
                    if not bu_customer_obj:
                        logger.error(f"customer {obj_id} is not available")

                    employee_obj = bu_customer_obj.business_unit_employee
                    if not employee_obj:
                        logger.error(f"customer {obj_id} is not an employee of business unit")
                    if scene == 'new_customer':
                        customer.bu_employee_id = employee_obj.id
                        customer.bu_id = employee_obj.business_unit_id
                else:
                    logger.error('二维码过期')
        elif kwargs.get('scene_invitation') and kwargs.get('scene'):
            scene = kwargs.get('scene')
            scene_invitation = kwargs.get('scene_invitation')
            if scene == 'new_fgp':
                if redis_db.exists(scene_invitation):
                    logger.debug("new_fgp action")
                    obj_json = json.loads(redis_db.get(scene_invitation))
                    obj_id = obj_json['gp_id']
                    salesman_id = obj_json['salesman_id']
                    redis_db.delete(scene_invitation)
                    gp_obj = FranchiseeGroupPurchase.query.get(obj_id)
                    sku_id = gp_obj.sku_id
                    sku = SKU.query.get(sku_id)
                    if sku and sku.status == 1 and sku.delete_at is None:
                        logger.debug("create fgp shop cart order")
                        cart_item = new_data_obj("ShoppingCart",
                                                 **{"customer_id": customer.id, "sku_id": sku_id, "delete_at": None,
                                                    "can_change": 0, "fgp_id": obj_id, "salesman_id": salesman_id})

                        if cart_item:
                            if cart_item['status']:
                                cart_item['obj'].quantity = gp_obj.amount
                            else:
                                cart_item['obj'].quantity += gp_obj.amount

                            logger.info(submit_return(f"购物车添加成功<{cart_item['obj'].id}>", "购物出添加失败"))
                        else:
                            logger.error(f"将<{sku_id}>添加规到购物车失败")
                    else:
                        logger.error(f"<{sku_id}>已下架")
                else:
                    logger.error("二维码失效")

        if kwargs.get('shared_id'):
            # 查找分享者是否存在
            shared_customer_ = Customers.query.filter(Customers.openid.__eq__(kwargs['shared_id']),
                                                      Customers.delete_at.__eq__(None)).first()
            if not shared_customer_:
                logger.error(f"{kwargs.get('shared_id')} is not exist!")
            else:
                shared_member_card = shared_customer_.member_card.filter_by(status=1, member_type=1).first()

                if shared_customer_.grade == 0:
                    # 仅直客可以获取分享积分
                    shared_customer_.total_points += SHARE_AWARD
                    new_data_obj("Scores", **{"id": make_uuid(),
                                              "customer_id": shared_customer_.id,
                                              "reason": f"share to {customer.id}",
                                              "quantity": SHARE_AWARD})

                if not customer.parent_id and new_customer['status']:
                    # 写入分享关系，不可修改
                    customer.parent_id = shared_customer_.id

                if not customer.interest_id and new_customer['status']:
                    if shared_member_card:
                        # 上级如果是代理商，interest_id，利益关系挂在上级ID
                        customer.interest_id = shared_customer_.id
                    else:
                        # 如果分享来自直客，interest_id，如果直客没有interest_id,则都没有利益关系
                        customer.interest_id = shared_customer_.interest_id

        # 查询并删除已经登陆的信息
        logged_in_info = customer.login_info.filter_by(platform="wechat", status=True).all()
        for lg in logged_in_info:
            db.session.delete(lg)
        db.session.flush()

        login_time = int(time.time())

        new_data_obj("LoginInfo",
                     **{
                         'token': session_key,
                         'login_time': login_time,
                         'login_ip': login_ip,
                         'customer': customer.id,
                         'platform': 'wechat',
                         'status': True
                     }
                     )
        db.session.add(customer)
        commit_result = session_commit()
        if commit_result.get("code") == "false":
            raise Exception(json.dumps(commit_result))

        ru = get_table_data_by_id(Customers, customer.id,
                                  ["role", "member_info", "first_page_popup", "job_role"],
                                  ["role_id"])

        logger.debug(f"login info {ru}")

        return success_return(data={'customer_info': ru, 'session_key': session_key}, message='登录成功')
    except Exception as e:
        traceback.print_exc()
        return false_return(data=str(e), message='登陆失败'), 400


def decode_auth_token(auth_token):
    """
    验证Token
    :param auth_token:
    :return: integer|string
    """
    try:
        payload = jwt.decode(auth_token, SECRET_KEY, leeway=datetime.timedelta(seconds=10))
        # 取消过期时间验证
        # payload = jwt.decode(auth_token, config.SECRET_KEY, options={'verify_exp': False})
        if 'data' in payload.keys() and 'id' in payload['data'].keys():
            return success_return(data=payload)
        else:
            raise jwt.InvalidTokenError
    except jwt.ExpiredSignatureError:
        return false_return(message='Token过期')
    except jwt.InvalidTokenError:
        return false_return(message='无效Token')


def identify(request):
    """
    用户鉴权
    :param: request
    :return: json
    """
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_token_arr = auth_header.split(" ")
        if not auth_token_arr or auth_token_arr[0] != 'Bearer' or len(auth_token_arr) != 2:
            result = false_return(message='请传递正确的验证头信息')
        else:
            auth_token = auth_token_arr[1]
            if not LoginInfo.query.filter_by(token=auth_token).first():
                return false_return(message='认证失败')
            payload = decode_auth_token(auth_token)
            if payload['code'] == 'success':
                data = payload['data']['data']
                user = Customers.query.filter_by(id=data['id']).first()
                if user is None:
                    result = false_return('', '找不到该用户信息')
                else:
                    login_info = LoginInfo.query.filter_by(token=auth_token, customer=user.id).first()
                    if login_info and login_info.login_time == data['login_time']:
                        result = success_return(data={"user": user, "login_info": login_info}, message='请求成功')
                    else:
                        result = false_return(message='Token已更改，请重新登录获取')
            else:
                result = false_return(message=payload['message'])
    else:
        result = false_return(message='没有提供认证token')
    return result
