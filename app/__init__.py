from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_apscheduler import APScheduler
import logging
import redis
import queue
from flask_sqlalchemy import SQLAlchemy as SQLAlchemyBase
from sqlalchemy.pool import NullPool
from flask_restplus import Api
from fdfs_client.client import *
from qcloudsms_py import SmsSingleSender, SmsMultiSender
import threading
from flask_cors import CORS
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix


class SQLAlchemy(SQLAlchemyBase):
    def apply_driver_hacks(self, app, info, options):
        super(SQLAlchemy, self).apply_driver_hacks(app, info, options)
        options['poolclass'] = NullPool
        options.pop('pool_size', None)


# 用于存放监控记录信息，例如UPS前序状态，需要配置持久化
redis_db = redis.Redis(host='localhost', port=6379, db=7, decode_responses=True)

db = SQLAlchemy()
scheduler = APScheduler()
sess = Session()
default_api = Api(title='Infinicalc API', version='v0.1', prefix='/api', contact='chjz1226@gmail.com')

# 用于处理订单建议书的队列
work_q = queue.Queue(maxsize=100)

# 用于处理请求request的队列
request_q = queue.Queue(maxsize=1000)

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
logger = logging.getLogger()
hdlr = logging.FileHandler("run.log")
formatter = logging.Formatter(fmt='%(asctime)s - %(module)s-%(funcName)s - %(levelname)s - %(message)s',
                              datefmt='%m/%d/%Y %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

# tracker_path = get_tracker_conf('/Users/Peter/fastdfs/client.conf')
# fastdfs_client = Fdfs_client(tracker_path)
SECRET_KEY = '12kid9k29dj3nd8_2323'

# 短信应用 SDK AppID
appid = 1400348279  # SDK AppID 以1400开头
# 短信应用 SDK AppKey
appkey = "b31aa540ae287f0bc9cbca1667cf3865"
# 需要发送短信的手机号码
phone_numbers = ["13817730962", "15962968250‬"]
# 短信模板ID，需要在短信控制台中申请
template_id = 572001  # NOTE: 这里的模板 ID`7839`只是示例，真实的模板 ID 需要在短信控制台中申请
# 签名
sms_sign = "Infinicalc"

ssender = SmsSingleSender(appid, appkey)

coupon_lock = threading.Lock()
order_lock = threading.Lock()
sku_lock = threading.Lock()


def create_app(config_name):
    app = Flask(__name__)
    # CORS(app)
    app.config.from_object(config[config_name])
    app.wsgi_app = ProxyFix(app.wsgi_app)
    config[config_name].init_app(app)
    db.app = app
    db.init_app(app)
    default_api.init_app(app)
    db.create_scoped_session()
    scheduler.init_app(app)
    sess.init_app(app)
    scheduler.start()

    # @default_api.errorhandler(Exception)
    # def generic_exception_handler(e: Exception):
    #     logger.error(">>>>>" + str(e))
    #     return {'message': f'Internal Server Error {e}'}, 500
    #
    # @app.errorhandler(Exception)
    # def app_generic_exception_handler(e: Exception):
    #     logger.error(">>>>>" + str(e))
    #     return {'message': f'Internal Server Error {e}'}, 500

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        if request.method == 'OPTIONS':
            response.headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT'
            headers = request.headers.get('Access-Control-Request-Headers')
            if headers:
                response.headers['Access-Control-Allow-Headers'] = headers
        return response

    from .users import users as users_blueprint
    app.register_blueprint(users_blueprint)

    from .roles import roles as roles_blueprint
    app.register_blueprint(roles_blueprint)

    from .mall import mall as mall_blueprint
    app.register_blueprint(mall_blueprint)

    from .elements import elements as elements_blueprint
    app.register_blueprint(elements_blueprint)

    from .layout import layout as layout_blueprint
    app.register_blueprint(layout_blueprint)

    from .sms import sms as sms_blueprint
    app.register_blueprint(sms_blueprint)

    from .customers import customers as customers_blueprint
    app.register_blueprint(customers_blueprint)

    from .promotion_groups import promotion_groups as promotion_groups_blueprint
    app.register_blueprint(promotion_groups_blueprint)

    from .promotions import promotions as promotions_blueprint
    app.register_blueprint(promotions_blueprint)

    from .shopping_cart import shopping_cart as shopping_cart_blueprint
    app.register_blueprint(shopping_cart_blueprint)

    from .banners import banners as banners_blueprint
    app.register_blueprint(banners_blueprint)

    from .obj_storage import obj_storage as obj_storage_blueprint
    app.register_blueprint(obj_storage_blueprint)

    from .invitation_code import invitation_code as invitation_code_blueprint
    app.register_blueprint(invitation_code_blueprint)

    from .member_cards import member_cards as member_cards_blueprint
    app.register_blueprint(member_cards_blueprint)

    from .wechat import wechat as wechat_blueprint
    app.register_blueprint(wechat_blueprint)

    from .cargoes import cargoes as cargoes_blueprint
    app.register_blueprint(cargoes_blueprint)

    from .packing_orders import packing_orders as packing_orders_blueprint
    app.register_blueprint(packing_orders_blueprint)

    from .news_center import news_center as news_center_blueprint
    app.register_blueprint(news_center_blueprint)

    from .news_sections import news_sections as news_sections_blueprint
    app.register_blueprint(news_sections_blueprint)

    from .orders import orders as orders_blueprint
    app.register_blueprint(orders_blueprint)

    from .refund_orders import refund as refund_blueprint
    app.register_blueprint(refund_blueprint)

    from .rebates import rebates as rebates_blueprint
    app.register_blueprint(refund_blueprint)

    from .item_orders import item_orders as item_orders_blueprint
    app.register_blueprint(item_orders_blueprint)

    from .scene_invitation import scene_invitation as scene_invitation_blueprint
    app.register_blueprint(scene_invitation_blueprint)

    from .wechat import wechat as wechat_blueprint
    app.register_blueprint(wechat_blueprint)

    # from .advertisements import advertisements as advertisements_blueprint
    # app.register_blueprint(advertisements_blueprint)

    from .business_units import business_units as business_unit_blueprint
    app.register_blueprint(business_unit_blueprint)

    from .franchisee import franchisee as franchisee_blueprint
    app.register_blueprint(franchisee_blueprint)

    from .items_verification import items_verification as iv_blueprint
    app.register_blueprint(iv_blueprint)

    from .wechat_purse import wechat_purse as wp_blueprint
    app.register_blueprint(wp_blueprint)

    from .deposit import deposit as deposit_blueprint
    app.register_blueprint(deposit_blueprint)

    from .express_orders import express_orders as express_orders_blueprint
    app.register_blueprint(express_orders_blueprint)

    return app
