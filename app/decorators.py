from functools import wraps
from flask import abort, request, make_response, session
from . import logger
from .common import false_return, exp_return, success_return
from app.auth.auths import identify
from app.frontstage_auth import auths
from flask import make_response
from app.models import Customers


def allow_cross_domain(fun):
    @wraps(fun)
    def wrapper_fun(*args, **kwargs):
        rst = make_response(fun(*args, **kwargs))
        rst.headers['Access-Control-Allow-Origin'] = '*'
        rst.headers['Access-Control-Allow-Methods'] = 'PUT,GET,POST,DELETE'
        allow_headers = "Referer,Accept,Origin,User-Agent"
        rst.headers['Access-Control-Allow-Headers'] = allow_headers
        return rst

    return wrapper_fun


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(
            'IP {} is checking login status'.format(
                request.headers.get('X-Forwarded-For', request.remote_addr)))
        if not identify(request).get('code') == "success":
            abort(make_response(false_return(message='用户未登陆'), 401))
        return f(*args, **kwargs)

    return decorated_function


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):

            def __check_front(permit):
                # 区分前后台，前端传递的permission为int类型，并且header中的Authorization 不包括Bearer关键字
                # 后端传递的permission为str类型，并且必须在header中的Authorization包括Bearer
                open_id = request.headers.get('Authorization')
                customer = Customers.query.filter(Customers.openid.__eq__(open_id), Customers.status.__eq__(1),
                                                  Customers.delete_at.__eq__(None)).first()
                if not customer or not customer.can(permit):
                    logger.warn('This user\'s action is not permitted!')
                    # abort(make_response(false_return(message='This user\'s action is not permitted!'), 403))
                    return false_return(message='This user\'s action is not permitted!')
                kwargs['current_user'] = customer
                session['current_user'] = customer.id
                return success_return()

            def __check_back(permit):
                # 处理后端用户
                current_user = identify(request)
                if current_user.get('code') == 'success' and 'logout' in permit:
                    kwargs['info'] = current_user['data']
                    kwargs['current_user'] = current_user['data']['user']
                    session['current_user'] = current_user['data']['user'].id
                    return success_return()

                if current_user.get("code") == "success" and "admin" not in [r.name for r in
                                                                             current_user['data']['user'].roles]:
                    if permit not in [p.permission for p in current_user['data']['user'].permissions]:
                        logger.warn('This user\'s action is not permitted!')
                        return false_return(message='This user\'s action is not permitted!')
                elif current_user.get("code") == "success" and "admin" in [r.name for r in
                                                                           current_user['data']['user'].roles]:
                    session['current_user'] = current_user['data']['user'].id
                    kwargs['info'] = current_user['data']
                    return success_return()

                else:
                    return exp_return(message=current_user.get("message"))

            check_result = dict()
            if 'Bearer' not in request.headers.get('Authorization'):
                # 说明是前端用户
                if isinstance(permission, list):
                    # 当permission为list时，表示这个接口是公共接口
                    for p in permission:
                        if isinstance(p, int):
                            check_result = __check_front(p)
                else:
                    if isinstance(permission, int):
                        check_result = __check_front(permission)
                if not check_result:
                    logger.error(check_result)
                    abort(make_response(false_return(message="权限配置错误，没有权限"), 403))
                elif check_result['code'] == 'false':
                    logger.error(check_result)
                    abort(make_response(check_result, 403))
            else:
                # 说明是后端用户
                if isinstance(permission, list):
                    # 当permission为list时，表示这个接口是公共接口
                    for p in permission:
                        if isinstance(p, str):
                            check_result = __check_back(p)
                else:
                    if isinstance(permission, str):
                        check_result = __check_back(permission)
                if not check_result:
                    logger.error(check_result)
                    abort(make_response(false_return(message="权限配置错误，没有权限"), 403))
                elif check_result['code'] != 'success':
                    logger.error(check_result)
                    abort(make_response(check_result, 403))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def permission_ip(permission_ip_list):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger.info(
                'IP {} is trying to get the api'.format(
                    request.headers.get('X-Forwarded-For', request.remote_addr)))
            if request.headers.get('X-Forwarded-For', request.remote_addr) not in permission_ip_list:
                abort(make_response(false_return(message='IP ' + request.remote_addr + ' not permitted')), 403)
            return f(*args, **kwargs)

        return decorated_function

    return decorator
