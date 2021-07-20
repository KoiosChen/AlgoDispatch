import jwt
import datetime
import time
from ..models import Users, LoginInfo
from .. import db, logger, SECRET_KEY
from ..common import success_return, false_return, session_commit, code_return, sort_by_order
from ..public_method import new_data_obj
from sqlalchemy import or_
from ..public_method import table_fields, get_table_data_by_id


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
        return false_return(message=str(e)), 400


def authenticate(username, password, login_ip, platform, method='password'):
    """
    用户登录，登录成功返回token，将登录时间写入数据库；登录失败返回失败原因
    :param username: 用户名、邮箱或者手机号
    :param password: 用户密码，或者是手机验证码
    :param login_ip: 用户发起请求的IP
    :param platform: pc | mobile
    :param method: default is password, or else use code
    code: using the phone number as username, cell phone message as password
    wechat: using wechat id as login username , password=?
    :return: json
    """
    verify_method = {
        'password': {"method": "verify_password", 'msg': '用户名密码不正确'},
        'code': {'method': 'verify_code', 'msg': '验证码错误'}
    }

    user_info = Users.query.filter(or_(Users.username.__eq__(username),
                                       Users.phone.__eq__(username),
                                       Users.email.__eq__(username)), Users.status.__eq__(1)).first()

    if user_info is None:
        return code_return(false_return(message='找不到用户'))

    # 查询并删除已经登陆的信息
    logged_in_info = user_info.login_info.filter_by(platform=platform, status=True).all()
    for lg in logged_in_info:
        db.session.delete(lg)
    session_commit()

    if getattr(user_info, verify_method[method]['method'])(password):
        login_time = int(time.time())
        token = encode_auth_token(user_info.id, login_time, login_ip, platform).decode()

        new_data_obj("LoginInfo",
                     **{
                         'token': token,
                         'login_time': login_time,
                         'login_ip': login_ip,
                         'platform': platform,
                         'user': user_info.id,
                         'status': True
                     }
                     )
        # db.session.add(user_info)
        session_commit()

        permissions = [u.permission for u in user_info.permissions if u.permission is not None]

        ru = get_table_data_by_id(Users, user_info.id, ["roles", "menus"], ["password_hash"])
        menus = ru.pop('menus')

        sort_by_order(menus)

        # permissions = ru.pop['permissions']
        return success_return(data={'token': token, 'menus': menus, 'permissions': permissions, 'user': ru},
                              message='登录成功')
    else:
        return false_return(message=verify_method[method]['msg']), 400


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
                user = Users.query.filter_by(id=data['id']).first()
                if user is None:
                    result = false_return('', '找不到该用户信息')
                else:
                    login_info = LoginInfo.query.filter_by(token=auth_token, user=user.id).first()
                    if login_info and login_info.login_time == data['login_time']:
                        result = success_return(data={"user": user, "login_info": login_info}, message='请求成功')
                    else:
                        result = false_return(message='Token已更改，请重新登录获取')
            else:
                result = payload
    else:
        result = false_return(message='没有提供认证token')
    return result
