from app import db, redis_db
import datetime
import os
import uuid
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


job_arguments = db.Table('job_arguments',
                         db.Column('job_id', db.String(64), db.ForeignKey('jobs.id'), primary_key=True),
                         db.Column('arguments_id', db.String(64), db.ForeignKey('arguments.id'),
                                   primary_key=True),
                         db.Column('create_at', db.DateTime, default=datetime.datetime.now))


class Classifies(db.Model):
    __tablename__ = 'classifies'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(50), nullable=False)
    jobs = db.relationship('Jobs', backref='classifies', lazy='dynamic')


class ArgName(db.Model):
    __tablename__ = 'arg_name'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(50), nullable=False, unique=True, index=True)
    values = db.relationship('Arguments', backref='arg_name', uselist=False)


class Arguments(db.Model):
    __tablename__ = 'arguments'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    arg_name_id = db.Column(db.String(64), db.ForeignKey('arg_name.id'))
    value = db.Column(db.String(50), nullable=False, index=True)


class Orders(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(100), index=True, comment="任务订单名称")
    desc = db.Column(db.String(200), comment="任务订单描述")
    parent_id = db.Column(db.String(64), db.ForeignKey('orders.id'))
    parent = db.relationship('Orders', backref="children", remote_side=[id])
    job_id = db.Column(db.String(64), db.ForeignKey('jobs.id'))
    run_times = db.Column(db.SmallInteger, default=0, comment='如果有下游job，则以此计数，通过children来获取其下游job')
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
    # creator_id = db.Column(db.String(64), db.ForeignKey('users.id'))
    seq = db.Column(db.SmallInteger, default=0, comment="同级任务中执行先后顺序")
    classify = db.Column(db.String(64), db.ForeignKey('classifies.id'))
    master = db.Column(db.String(20), comment='Kubernetes Master Name')

    parent_id = db.Column(db.String(64), db.ForeignKey('jobs.id'))
    parent = db.relationship('Jobs', backref="children", remote_side=[id])

    config_files = db.relationship('ConfigFiles', backref='job', uselist=False)

    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)
    #
    arguments = db.relationship(
        'Arguments',
        secondary=job_arguments,
        backref=db.backref('related_jobs')
    )

    orders = db.relationship('Orders', backref='related_jobs', lazy='dynamic')


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


class ConfigFiles(db.Model):
    __tablename__ = 'config_files'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    filename = db.Column(db.String(100), index=True)
    storage = db.Column(db.String(200), index=True)
    job_id = db.Column(db.String(64), db.ForeignKey('jobs.id'))
    status = db.Column(db.SmallInteger, default=1, comment='1,正常，0, 停用')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


FDFS_URL = "http://shaxyxa-fdfs01.xyxa.cnsh.algospace.org/"

aes_key = 'koiosr2d2c3p0000'

RECHARGE_REBATE_POLICY = 3

FIRST_PAGE_POPUP_URL = "IMAGE"

PermissionIP = redis_db.lrange('permission_ip', 0, -1)

PATH_PREFIX = os.path.abspath(os.path.dirname(__file__))

KubeMaster = {'k8sm01': os.path.join(PATH_PREFIX, "conf/k8sm01_admin.yaml"),
              'k8sm02': os.path.join(PATH_PREFIX, "conf/k8sm02_admin.yaml")}

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
