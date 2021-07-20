from app import db, redis_db
import datetime
import os
import uuid
from sqlalchemy import UniqueConstraint
import random


def make_uuid():
    return str(uuid.uuid4())


def make_order_id(prefix=None):
    """
    生成订单号
    :return:
    """
    date = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    # 生成4为随机数作为订单号的一部分
    random_str = str(random.randint(1, 9999))
    random_str = random_str.rjust(4, '0')
    rtn = '%s%s' % (date, random_str)
    return rtn if prefix is None else prefix + rtn


user_role = db.Table('user_role',
                     db.Column('user_id', db.String(64), db.ForeignKey('users.id'), primary_key=True),
                     db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
                     db.Column('create_at', db.DateTime, default=datetime.datetime.now))

customer_role = db.Table('customer_role',
                         db.Column('customer_id', db.String(64), db.ForeignKey('customers.id'), primary_key=True),
                         db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
                         db.Column('create_at', db.DateTime, default=datetime.datetime.now))

spu_standards = db.Table('spu_standards',
                         db.Column('spu_id', db.String(64), db.ForeignKey('spu.id'), primary_key=True),
                         db.Column('standards_id', db.String(64), db.ForeignKey('standards.id'),
                                   primary_key=True),
                         db.Column('create_at', db.DateTime, default=datetime.datetime.now))

job_arguments = db.Table('job_arguments',
                         db.Column('job_id', db.String(64), db.ForeignKey('jobs.id'), primary_key=True),
                         db.Column('arguments_id', db.String(64), db.ForeignKey('arguments.id'),
                                   primary_key=True),
                         db.Column('create_at', db.DateTime, default=datetime.datetime.now))

job_orders = db.Table('job_orders',
                      db.Column('job_id', db.String(64), db.ForeignKey('job.id'), primary_key=True),
                      db.Column('orders_id', db.String(64), db.ForeignKey('orders.id'), primary_key=True),
                      db.Column('create_at', db.DateTime, default=datetime.datetime.now))



class OptionsDict(db.Model):
    __tablename__ = 'options_dic'
    id = db.Column(db.Integer, primary_key=True)
    # 字典名称
    name = db.Column(db.String(30), nullable=False, index=True)
    # 字典查询主键
    key = db.Column(db.String(80), nullable=False, index=True)
    label = db.Column(db.String(20), nullable=False, index=True)
    value = db.Column(db.String(5), nullable=False, index=True)
    order = db.Column(db.SmallInteger)
    status = db.Column(db.Boolean, default=True)
    selected = db.Column(db.Boolean, default=False)
    type = db.Column(db.String(20))
    memo = db.Column(db.String(100))
    __table_args__ = (UniqueConstraint('key', 'label', name='_key_label_combine'),)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)


class Permission:
    USER = 0x01
    MEMBER = 0x02
    VIP_MEMBER = 0x04
    BU_WAITER = 0x08
    BU_OPERATOR = 0x10
    BU_MANAGER = 0x20
    FRANCHISEE_OPERATOR = 0x40
    FRANCHISEE_MANAGER = 0x80
    CUSTOMER_SERVICE = 0x100
    ADMINISTRATOR = 0x200


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(64), primary_key=True, default=str(uuid.uuid4()))
    email = db.Column(db.String(64), unique=True, index=True)
    phone = db.Column(db.String(15), unique=True, index=True)
    wechat_id = db.Column(db.String(50), unique=True, index=True)
    username = db.Column(db.String(64), index=True, unique=True)
    true_name = db.Column(db.String(30))
    # 0 unknown, 1 male, 2 female
    gender = db.Column(db.SmallInteger)
    roles = db.relationship(
        'Roles',
        secondary=user_role,
        backref=db.backref(
            'users'
        )
    )
    password_hash = db.Column(db.String(128))
    status = db.Column(db.SmallInteger)
    post = db.relationship('Post', backref='author', lazy='dynamic')
    address = db.Column(db.String(200))
    login_info = db.relationship('LoginInfo', backref='login_user', lazy='dynamic')

    @property
    def permissions(self):
        return Permissions.query.outerjoin(Menu).outerjoin(role_menu).outerjoin(Roles).outerjoin(user_role).outerjoin(
            Users).filter(Users.id.__eq__(self.id)).all()

    @property
    def menus(self):
        return Menu.query.outerjoin(role_menu).outerjoin(Roles).outerjoin(user_role).outerjoin(Users). \
            filter(
            Users.id == self.id
        ).order_by(Menu.order).all()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        self.token = None

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def verify_code(self, message):
        """
        验证码
        :param message:
        :return:
        """
        login_key = f"{self.id}::{self.phone}::login_message"
        return True if redis_db.exists(login_key) and redis_db.get(login_key) == message else False

    def __repr__(self):
        return '<User %r>' % self.username


class Roles(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)

    def __repr__(self):
        return '<Role %r>' % self.name


class LoginInfo(db.Model):
    __tablename__ = 'login_info'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(500), nullable=False)
    login_time = db.Column(db.Integer, nullable=False)
    platform = db.Column(db.String(20), nullable=False)
    login_ip = db.Column(db.String(64))
    user = db.Column(db.String(64), db.ForeignKey('users.id'))
    customer = db.Column(db.String(64), db.ForeignKey('customers.id'))
    status = db.Column(db.Boolean, default=True)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class Classifies(db.Model):
    __tablename__ = 'classifies'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(50), nullable=False)
    spu = db.relationship('SPU', backref='classifies', lazy='dynamic')


class ArgName(db.Model):
    __tablename__ = 'meta_name'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(50), nullable=False, unique=True, index=True)
    values = db.relationship('Arguments', backref='arg_name', uselist=False)


class Arguments(db.Model):
    __tablename__ = 'arguments'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    arg_name_id = db.Column(db.String(64), db.ForeignKey('meta_name.id'))
    value = db.Column(db.String(50), nullable=False, unique=True, index=True)


class JobGroup(db.Model):
    __tablename__ = 'job_group'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(100), nullable=False, index=True)
    sub_name = db.Column(db.String(100))
    express_fee = db.Column(db.DECIMAL(6, 2), default=0.00, comment="邮费，默认0元")
    contents = db.Column(db.Text(length=(2 ** 32) - 1))
    standards = db.relationship(
        'Standards',
        secondary=spu_standards,
        backref=db.backref(
            'spu'
        )
    )
    classify_id = db.Column(db.String(64), db.ForeignKey('classifies.id'))
    sku = db.relationship('SKU', backref='the_spu', lazy='dynamic')
    status = db.Column(db.SmallInteger, default=0, comment="1 上架； 0 下架")
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class Orders(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(100), index=True, comment="任务订单名称")
    desc = db.Column(db.String(200), comment="任务订单描述")
    upstream_id = db.Column(db.String(64), db.ForeignKey('jobs.id'))
    job_id = db.Column(db.String(64), db.ForeignKey('jobs.id'))
    status = db.Column(db.SmallInteger, default=1)
    output = db.Column(db.String(200), comment="输出结果")
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class Jobs(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(100), nullable=False, index=True, comment="创建job的用户下不可重名，由程序控制")
    desc = db.Column(db.String(200), comment="任务描述")
    run_env = db.Column(db.String(100), default='K8S', comment="任务运行类型，例如K8S，vsphere等")
    run_type = db.Column(db.String(100), default='job', comment='job, crontab, once')
    input_params = db.Column(db.String(200), comment="任务输入参数")
    status = db.Column(db.SmallInteger, default=0, comment="1 可用； 0 暂停使用")
    creator_id = db.Column(db.String(64), db.ForeignKey('users.id'))
    seq = db.Column(db.SmallInteger, default=0, comment="同级任务中执行先后顺序")

    parent_id = db.Column(db.String(64), db.ForeignKey('jobs.id'))
    parent = db.relationship('Jobs', backref="children", remote_side=[id])

    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)
    #
    arguments = db.relationship(
        'Arguments',
        secondary=job_arguments,
        backref=db.backref('related_jobs')
    )

    orders = db.relationship(
        'JobOrders',
        secondary=job_orders,
        backref=db.backref('related_jobs')
    )


class SMSTemplate(db.Model):
    __tablename__ = 'sms_template'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    template_id = db.Column(db.String(64), nullable=False)
    platform = db.Column(db.String(100), default='tencent', nullable=False)
    content = db.Column(db.String(140))
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)


class SMSSign(db.Model):
    __tablename__ = 'sms_sign'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    sign_id = db.Column(db.String(64), nullable=False)
    content = db.Column(db.String(140))
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)


class SMSApp(db.Model):
    __tablename__ = 'sms_app'
    id = db.Column(db.Integer, primary_key=True)
    app_id = db.Column(db.String(64), nullable=False, index=True)
    app_key = db.Column(db.String(64), nullable=False, index=True)
    platform = db.Column(db.String(100), default='tencent', nullable=False)
    status = db.Column(db.SmallInteger, default=1, comment="1正常；2暂停")
    callback_url = db.Column(db.String(100), comment="短信回调URL")
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)


class ObjStorage(db.Model):
    """
    存放对象存储的结果
    """
    __tablename__ = 'obj_storage'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    bucket = db.Column(db.String(64), nullable=False, index=True)
    region = db.Column(db.String(64), nullable=False, index=True)
    obj_key = db.Column(db.String(64), nullable=False, index=True)
    obj_type = db.Column(db.SmallInteger, default=0, comment="0 图片，1 视频， 2 文本")
    url = db.Column(db.String(150), nullable=False, index=True)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    parent_id = db.Column(db.String(64), db.ForeignKey('obj_storage.id'))
    parent = db.relationship('ObjStorage', backref="thumbnails", remote_side=[id])

    banners = db.relationship('Banners', backref='banner_contents', lazy='dynamic')
    coupons = db.relationship('Coupons', backref="icon_objects", lazy='dynamic')
    evaluates = db.relationship("Evaluates", backref="experience_objects", lazy='dynamic')
    brands = db.relationship('Brands', backref='logo_objects', lazy='dynamic')
    # customers = db.relationship('Customers', backref='photo_objects', lazy='dynamic')
    news_center = db.relationship('NewsCenter', backref='news_cover_image', lazy='dynamic')
    advertisement = db.relationship('Advertisements', backref='ad_image', uselist=False)


aes_key = 'koiosr2d2c3p0000'

RECHARGE_REBATE_POLICY = 3

FIRST_PAGE_POPUP_URL = "IMAGE"

PermissionIP = redis_db.lrange('permission_ip', 0, -1)

PATH_PREFIX = os.path.abspath(os.path.dirname(__file__))

CERT_PATH = PATH_PREFIX + '/cert/apiclient_cert.pem'

KEY_PATH = PATH_PREFIX + '/cert/apiclient_key.pem'

CONFIG_FILE_PATH = PATH_PREFIX + 'config_file/'

CACTI_PIC_FOLDER = PATH_PREFIX + '/static/cacti_pic/'

REQUEST_RETRY_TIMES = 1
REQUEST_RETRY_TIMES_PER_TIME = 1

NEW_ONE_SCORES = 0
SHARE_AWARD = 0

REDIS_LONG_EXPIRE = 1800
REDIS_24H = 86400
REDIS_SHORT_EXPIRE = 300
