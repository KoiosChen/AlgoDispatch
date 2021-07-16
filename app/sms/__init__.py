from flask import Blueprint

sms = Blueprint('sms', __name__)

from . import sms_template, sms_app, sms_api, verify_code
