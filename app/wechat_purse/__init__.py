from flask import Blueprint

wechat_purse = Blueprint('wechat_purse', __name__)

from . import wechat_purse_api
