import random
from .. import ssender, redis_db
from qcloudsms_py.httpclient import HTTPError
from ..common import success_return, false_return


def general_verification_code(code_len=6):
    code = ""
    for _ in range(code_len):
        code += str(random.randint(1, 9))
    return code


def send_verification_code(phone, stage, template_id='576515', sms_sign='泛渤通信'):
    code = general_verification_code()
    params = [code, '2']
    key = f"{stage}::verification_code::{phone}"
    try:
        result = ssender.send_with_param(86, phone, template_id, params, sign=sms_sign, extend="", ext="")
        redis_db.set(key, code)
        redis_db.expire(key, 305)
    except HTTPError as e:
        return false_return(message=f"短信发送失败，HTTPError: {e}"), 400
    except Exception as e:
        return false_return(message=f"短信发送失败，{e}"), 400
    return success_return(data=result, message="短信已发送")
