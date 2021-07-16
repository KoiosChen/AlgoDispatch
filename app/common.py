from . import db, logger
from collections import defaultdict
from sqlalchemy.exc import SQLAlchemyError


def success_return(data="", message=""):
    return {"code": "success", "data": data, "message": message}


def false_return(data="", message=""):
    return {"code": "false", "data": data, "message": message}


def code_return(msg, code=400):
    return msg, code


def exp_return(data="", message=""):
    return {"code": "exp", "data": data, "message": message}


def session_commit():
    try:
        db.session.commit()
        return success_return(message="db commit success")
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"users::register::db_commit()::SQLAlchemyError --> {str(e)}")
        return false_return(message=str(e)), 400


def submit_return(success_msg, false_msg):
    if session_commit().get("code") == "success":
        return success_return(message=success_msg)
    else:
        return false_return(message=false_msg + ", " + session_commit().get('message')), 400


def nesteddict():
    """
    构造一个嵌套的字典
    :return:
    """
    return defaultdict(nesteddict)


def sort_by_order(ms):
    ms.sort(key=lambda x: x['order'])
    for el in ms:
        if el.get('children'):
            sort_by_order(el['children'])
