from flask import current_app
from app import db, redis_db
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from sqlalchemy import UniqueConstraint
import random
from decimal import Decimal


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

roles_elements = db.Table('roles_elements',
                          db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
                          db.Column('element_id', db.Integer, db.ForeignKey('elements.id'), primary_key=True),
                          db.Column('create_at', db.DateTime, default=datetime.datetime.now))

spu_standards = db.Table('spu_standards',
                         db.Column('spu_id', db.String(64), db.ForeignKey('spu.id'), primary_key=True),
                         db.Column('standards_id', db.String(64), db.ForeignKey('standards.id'),
                                   primary_key=True),
                         db.Column('create_at', db.DateTime, default=datetime.datetime.now))

sku_standardvalue = db.Table('sku_standardvalue',
                             db.Column('sku_id', db.String(64), db.ForeignKey('sku.id'), primary_key=True),
                             db.Column('standardvalue_id', db.String(64), db.ForeignKey('standard_value.id'),
                                       primary_key=True),
                             db.Column('create_at', db.DateTime, default=datetime.datetime.now))

bu_decorate_images = db.Table('bu_decorate_images',
                              db.Column('bu_id', db.String(64), db.ForeignKey('business_units.id'), primary_key=True),
                              db.Column('obj_id', db.String(64), db.ForeignKey('obj_storage.id'), primary_key=True),
                              db.Column('create_at', db.DateTime, default=datetime.datetime.now)
                              )

deposit_images = db.Table('deposit_images',
                          db.Column('bu_id', db.String(64), db.ForeignKey('deposit.id'), primary_key=True),
                          db.Column('obj_id', db.String(64), db.ForeignKey('obj_storage.id'), primary_key=True),
                          db.Column('create_at', db.DateTime, default=datetime.datetime.now)
                          )

bu_products_images = db.Table('bu_products_images',
                              db.Column('bu_products_id', db.String(64), db.ForeignKey('business_unit_products.id'),
                                        primary_key=True),
                              db.Column('obj_id', db.String(64), db.ForeignKey('obj_storage.id'), primary_key=True),
                              db.Column('create_at', db.DateTime, default=datetime.datetime.now)
                              )

sku_obj = db.Table('sku_obj',
                   db.Column('sku_id', db.String(64), db.ForeignKey('sku.id'), primary_key=True),
                   db.Column('obj_id', db.String(64), db.ForeignKey('obj_storage.id'), primary_key=True),
                   db.Column('create_at', db.DateTime, default=datetime.datetime.now))

spu_obj = db.Table('spu_obj',
                   db.Column('spu_id', db.String(64), db.ForeignKey('spu.id'), primary_key=True),
                   db.Column('obj_id', db.String(64), db.ForeignKey('obj_storage.id'), primary_key=True),
                   db.Column('create_at', db.DateTime, default=datetime.datetime.now))

cargo_obj = db.Table('cargo_obj',
                     db.Column('cargo_id', db.String(64), db.ForeignKey('total_cargoes.id'), primary_key=True),
                     db.Column('obj_id', db.String(64), db.ForeignKey('obj_storage.id'), primary_key=True),
                     db.Column('create_at', db.DateTime, default=datetime.datetime.now))

refund_images = db.Table('refund_images',
                         db.Column('refund_id', db.String(64), db.ForeignKey('refund.id'), primary_key=True),
                         db.Column('obj_id', db.String(64), db.ForeignKey('obj_storage.id'), primary_key=True),
                         db.Column('create_at', db.DateTime, default=datetime.datetime.now))

sku_shoporders = db.Table('sku_shoporders',
                          db.Column('sku_id', db.String(64), db.ForeignKey('sku.id'), primary_key=True),
                          db.Column('shoporders_id', db.String(64), db.ForeignKey('shop_orders.id'), primary_key=True),
                          db.Column('create_at', db.DateTime, default=datetime.datetime.now))

benefits_gifts = db.Table('benefits_gifts',
                          db.Column('benefits_id', db.String(64), db.ForeignKey('benefits.id'), primary_key=True),
                          db.Column('gifts_id', db.String(64), db.ForeignKey('gifts.id'), primary_key=True),
                          db.Column('create_at', db.DateTime, default=datetime.datetime.now))

promotions_benefits = db.Table('promotions_benefits',
                               db.Column('promotions_id', db.String(64), db.ForeignKey('promotions.id'),
                                         primary_key=True),
                               db.Column('benefits_id', db.String(64), db.ForeignKey('benefits.id'), primary_key=True),
                               db.Column('create_at', db.DateTime, default=datetime.datetime.now))

promotions_brands = db.Table('promotions_brands',
                             db.Column('promotions_id', db.String(64), db.ForeignKey('promotions.id'),
                                       primary_key=True),
                             db.Column('brands_id', db.String(64), db.ForeignKey('brands.id'), primary_key=True),
                             db.Column('create_at', db.DateTime, default=datetime.datetime.now))

promotions_spu = db.Table('promotions_spu',
                          db.Column('promotions_id', db.String(64), db.ForeignKey('promotions.id'), primary_key=True),
                          db.Column('spu_id', db.String(64), db.ForeignKey('spu.id'), primary_key=True),
                          db.Column('create_at', db.DateTime, default=datetime.datetime.now))

promotions_sku = db.Table('promotions_sku',
                          db.Column('promotions_id', db.String(64), db.ForeignKey('promotions.id'), primary_key=True),
                          db.Column('sku_id', db.String(64), db.ForeignKey('sku.id'), primary_key=True),
                          db.Column('create_at', db.DateTime, default=datetime.datetime.now))

promotions_classifies = db.Table('promotions_classifies',
                                 db.Column('promotions_id', db.String(64), db.ForeignKey('promotions.id'),
                                           primary_key=True),
                                 db.Column('classifies_id', db.String(64), db.ForeignKey('classifies.id'),
                                           primary_key=True),
                                 db.Column('create_at', db.DateTime, default=datetime.datetime.now))

itemsorders_benefits = db.Table('itemsorders_benefits',
                                db.Column('itemsorders_id', db.String(64), db.ForeignKey('items_orders.id'),
                                          primary_key=True),
                                db.Column('benefits_id', db.String(64), db.ForeignKey('benefits.id'),
                                          primary_key=True),
                                db.Column('create_at', db.DateTime, default=datetime.datetime.now))

scene_member_cards = db.Table('scene_member_cards',
                              db.Column('scene_invitation_id', db.String(64), db.ForeignKey('scene_invitation.id'),
                                        primary_key=True),
                              db.Column('member_card_id', db.String(64), db.ForeignKey('member_cards.id'),
                                        primary_key=True),
                              db.Column('create_at', db.DateTime, default=datetime.datetime.now))

new_customer_awards_coupons = db.Table('new_customer_awards_coupons',
                                       db.Column('new_customer_awards_id',
                                                 db.Integer, db.ForeignKey('new_customer_awards.id'),
                                                 primary_key=True),
                                       db.Column('awards_coupon_id', db.String(64), db.ForeignKey('coupons.id'),
                                                 primary_key=True),
                                       db.Column('create_at', db.DateTime, default=datetime.datetime.now))

member_policy_bounce_coupons = db.Table('member_policy_bounce_coupons',
                                        db.Column('member_policy_id',
                                                  db.String(64), db.ForeignKey('member_policies.id'),
                                                  primary_key=True),
                                        db.Column('bounce_coupon_id', db.String(64), db.ForeignKey('coupons.id'),
                                                  primary_key=True),
                                        db.Column('create_at', db.DateTime, default=datetime.datetime.now))


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


class Roles(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    elements = db.relationship(
        'Elements',
        secondary=roles_elements,
        backref=db.backref(
            'elements_roles',
            lazy='dynamic'
        )
    )

    def __repr__(self):
        return '<Role %r>' % self.name


class CustomerRoles(db.Model):
    __tablename__ = 'customer_roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    customers = db.relationship('Customers', backref='role', lazy='dynamic')
    franchisee_operators = db.relationship('FranchiseeOperators', backref='role', lazy='dynamic')
    business_employee = db.relationship('BusinessUnitEmployees', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'USER': (Permission.USER, True),
            'MEMBER': (Permission.USER |
                       Permission.MEMBER, False),
            'VIP_MEMBER': (Permission.USER |
                           Permission.MEMBER |
                           Permission.VIP_MEMBER, False),
            'BU_WAITER': (Permission.USER |
                          Permission.MEMBER |
                          Permission.VIP_MEMBER |
                          Permission.BU_WAITER, False),
            'BU_OPERATOR': (Permission.USER |
                            Permission.MEMBER |
                            Permission.VIP_MEMBER |
                            Permission.BU_WAITER |
                            Permission.BU_OPERATOR, False),
            'BU_MANAGER': (Permission.USER |
                           Permission.MEMBER |
                           Permission.VIP_MEMBER |
                           Permission.BU_WAITER |
                           Permission.BU_OPERATOR |
                           Permission.BU_MANAGER, False),
            'FRANCHISEE_OPERATOR': (Permission.USER |
                                    Permission.MEMBER |
                                    Permission.VIP_MEMBER |
                                    Permission.FRANCHISEE_OPERATOR, False),
            'FRANCHISEE_MANAGER': (Permission.USER |
                                   Permission.MEMBER |
                                   Permission.VIP_MEMBER |
                                   Permission.FRANCHISEE_OPERATOR |
                                   Permission.FRANCHISEE_MANAGER, False),
            'CUSTOMER_SERVICE': (
            Permission.USER | Permission.MEMBER | Permission.VIP_MEMBER | Permission.CUSTOMER_SERVICE, False),
            'ADMINISTRATOR': (0xfff, False)
        }
        for r in roles:
            role = CustomerRoles.query.filter_by(name=r).first()
            if role is None:
                role = CustomerRoles(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class FranchiseeScopes(db.Model):
    __tablename__ = "franchisee_scopes"
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    province = db.Column(db.String(64))
    city = db.Column(db.String(64))
    district = db.Column(db.String(64))
    street = db.Column(db.String(64))
    franchisee_id = db.Column(db.String(64), db.ForeignKey("franchisees.id"))
    transaction_price = db.Column(db.DECIMAL(11, 2), comment='当前交易价格')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"{self.province}, {self.city}, {self.district}"


class ScopeDefinition(db.Model):
    __tablename__ = "scope_definition"
    id = db.Column(db.Integer, primary_key=True)
    province = db.Column(db.String(64))
    city = db.Column(db.String(10), nullable=False, index=True, comment='定义级别市及区')
    level = db.Column(db.SmallInteger, index=True, comment='区域级别，1-10')
    city_price = db.Column(db.DECIMAL(11, 2), index=True, comment='市级定价')
    district_price = db.Column(db.DECIMAL(11, 2), index=True, comment='区级定价')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Scope Definition: {self.city}: {self.city_price}>'


class Franchisees(db.Model):
    __tablename__ = "franchisees"
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(50), comment="加盟商名称")
    desc = db.Column(db.String(200), comment="描述")
    level = db.Column(db.SmallInteger, default=1, comment='默认1级，2 表示二级，一次类推')
    phone1 = db.Column(db.String(15), comment="加盟商联系电话1")
    phone2 = db.Column(db.String(15), comment="加盟商联系电话2")
    address = db.Column(db.String(100), comment="加盟商营业地址")
    bank_name = db.Column(db.String(50), comment="开户行名称")
    bank_account = db.Column(db.String(20), comment='银行账号')
    payee = db.Column(db.String(30), comment='收款人名称')
    tax_account = db.Column(db.String(20), comment='税号')
    bu_purchase_order_id = db.Column(db.String(64), db.ForeignKey("business_purchase_orders.id"))
    scopes = db.relationship("FranchiseeScopes", backref='franchisee', lazy="dynamic")
    operators = db.relationship("FranchiseeOperators", backref='franchisee', lazy="dynamic")
    down_streams = db.relationship("BusinessUnits", backref='franchisee', lazy="dynamic")
    inventory = db.relationship("FranchiseeInventory", backref='franchisee', lazy="dynamic")
    status = db.Column(db.SmallInteger, default=0, comment='0 待审核，1 审核通过 2 审核失败')

    # 代理商级联关系
    parent_id = db.Column(db.String(64), db.ForeignKey('franchisees.id'))
    parent = db.relationship('Franchisees', backref="children", remote_side=[id])

    fgps = db.relationship('FranchiseeGroupPurchase', backref='franchisee', lazy='dynamic')

    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class FranchiseeInventory(db.Model):
    __tablename__ = "franchisee_inventory"
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    sku_id = db.Column(db.String(64), db.ForeignKey('sku.id'))
    franchisee_id = db.Column(db.String(64), db.ForeignKey('franchisees.id'))
    amount = db.Column(db.Integer, index=True, default=0, comment="库存数量")
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class FranchiseeOperators(db.Model):
    __tablename__ = "franchisee_operators"
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(20), comment="员工姓名")
    age = db.Column(db.SmallInteger, comment="年龄")
    phone = db.Column(db.String(15))
    phone_validated = db.Column(db.Boolean, default=False)
    job_desc = db.Column(db.Integer, db.ForeignKey("customer_roles.id"))
    customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    franchisee_id = db.Column(db.String(64), db.ForeignKey('franchisees.id'))
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)

    bus = db.relationship("BusinessUnits", backref='operator', lazy='dynamic')


class FranchiseePurchaseOrders(db.Model):
    __tablename__ = "franchisee_purchase_orders"
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    franchisee_id = db.Column(db.String(64), db.ForeignKey('franchisees.id'))
    sku_id = db.Column(db.String(64), db.ForeignKey('sku.id'))
    amount = db.Column(db.SmallInteger, comment="进货或者出货量，进货为正数， 出货为负数")
    original_order_id = db.Column(db.String(64), db.ForeignKey('purchase_info.id'))
    purchase_from = db.Column(db.String(64), default="ShengZhuanJiuYe", comment="购入方，默认为盛馔酒业，代表总部")
    sell_to = db.Column(db.String(64), db.ForeignKey('business_units.id'))
    express_order_id = db.Column(db.String(64), db.ForeignKey('cloudwine_express_orders.id'))
    operate_at = db.Column(db.DateTime, comment='进出货日期')
    operator = db.Column(db.String(64), db.ForeignKey('customers.id'), comment="操作员")
    status = db.Column(db.SmallInteger, default=0, comment='0: 已发货未确认，1：已发货已确认, 2:已发货未收到, 3 未发货')
    bu_purchase_order = db.relationship("BusinessPurchaseOrders", backref="original_order", uselist=False)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class BusinessPurchaseOrders(db.Model):
    __tablename__ = "business_purchase_orders"
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    bu_id = db.Column(db.String(64), db.ForeignKey('business_units.id'))
    sku_id = db.Column(db.String(64), db.ForeignKey('sku.id'))
    amount = db.Column(db.SmallInteger, comment="进货或者出货量")
    express_order_id = db.Column(db.String(64), db.ForeignKey('cloudwine_express_orders.id'))
    original_order_id = db.Column(db.String(64), db.ForeignKey('franchisee_purchase_orders.id'))
    sell_to = db.Column(db.String(64), db.ForeignKey('customers.id'))
    status = db.Column(db.SmallInteger, default=0, comment='0: 已发货未确认，1：已发货已确认, 2:已发货未收到, 3:未发货')
    operator = db.Column(db.String(64), db.ForeignKey('customers.id'), comment="操作员")
    operate_at = db.Column(db.DateTime)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class BusinessUnits(db.Model):
    __tablename__ = 'business_units'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(50))
    desc = db.Column(db.String(200), comment="店铺介绍")
    chain_store_code = db.Column(db.String(20), comment="如果不为空，则以此code作为连锁店关键字")
    address = db.Column(db.String(100), comment="店铺地址", index=True)
    nation = db.Column(db.String(20), comment="国家", index=True)
    province = db.Column(db.String(20), comment="省份", index=True)
    city = db.Column(db.String(20), comment="城市", index=True)
    district = db.Column(db.String(20), comment="区", index=True)
    street = db.Column(db.String(50), comment="街道", index=True)
    street_number = db.Column(db.String(10), comment="门牌", index=True)
    phone1 = db.Column(db.String(20), comment="店铺电话1")
    phone2 = db.Column(db.String(20), comment="店铺电话2")
    unit_type = db.Column(db.SmallInteger, default=1, comment="店铺类型，默认为1，餐饮店")
    level = db.Column(db.SmallInteger, default=0, comment="评级，默认为0")
    mark = db.Column(db.Float, default=0.0, comment="评分")
    objects = db.relationship(
        'ObjStorage',
        secondary=bu_decorate_images,
        backref=db.backref('bu')
    )
    longitude = db.Column(db.String(20), comment='经度', index=True)
    latitude = db.Column(db.String(20), comment='纬度', index=True)
    bu_inventories = db.relationship("BusinessUnitInventory", backref='bu', lazy='dynamic')
    employees = db.relationship("BusinessUnitEmployees", backref='business_unit', lazy='dynamic')
    consumers = db.relationship("Customers", backref='business_unit', lazy='dynamic')
    products = db.relationship("BusinessUnitProducts", backref='producer', lazy='dynamic')
    deposits = db.relationship("Deposit", backref='bu', uselist=False)
    franchisee_id = db.Column(db.String(64), db.ForeignKey('franchisees.id'))
    franchisee_operator_id = db.Column(db.String(64), db.ForeignKey('franchisee_operators.id'))
    status = db.Column(db.SmallInteger, default=0, comment='1: 上架， 2: 下架。 若需要删除，写入delete_at时间')
    purchase_orders = db.relationship("BusinessPurchaseOrders", backref='bu', uselist=False)
    verify_orders = db.relationship('ItemVerification', backref='bu', lazy='dynamic')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<Unit name: %r>' % self.name


class BusinessUnitProducts(db.Model):
    __tablename__ = 'business_unit_products'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(10), comment="商品名称")
    desc = db.Column(db.String(50), comment="商品介绍")
    price = db.Column(db.DECIMAL(11, 2), default=0.00, comment='商品价格')
    objects = db.relationship(
        'ObjStorage',
        secondary=bu_products_images,
        backref=db.backref('bup')
    )
    bu_id = db.Column(db.String(64), db.ForeignKey('business_units.id'))
    order = db.Column(db.SmallInteger, default=0, comment='商品显示排序，默认0不排序')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<Product name: %r>' % self.name


class BusinessUnitEmployees(db.Model):
    __tablename__ = "business_unit_employees"
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(20), comment="员工姓名")
    age = db.Column(db.SmallInteger, comment="年龄")
    phone = db.Column(db.String(15))
    phone_validated = db.Column(db.Boolean, default=False)
    job_desc = db.Column(db.Integer, db.ForeignKey('customer_roles.id'))
    customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    business_unit_id = db.Column(db.String(64), db.ForeignKey('business_units.id'))
    consumers = db.relationship("Customers", backref='bu_inviter', lazy='dynamic',
                                foreign_keys='Customers.bu_employee_id')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<Employee name: %r>' % self.name


class BusinessUnitInventory(db.Model):
    __tablename__ = "business_unit_inventory"
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    sku_id = db.Column(db.String(64), db.ForeignKey('sku.id'))
    bu_id = db.Column(db.String(64), db.ForeignKey('business_units.id'))
    amount = db.Column(db.Integer, index=True, default=0, comment="库存数量")
    deposit = db.Column(db.Integer, index=True, default=0, comment="寄存量")
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class Deposit(db.Model):
    __tablename__ = "deposit"
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    sku_id = db.Column(db.String(64), db.ForeignKey('sku.id'))
    objects = db.relationship(
        'ObjStorage',
        secondary=deposit_images,
        backref=db.backref('obj_deposit')
    )
    deposit_status = db.Column(db.SmallInteger, default=0, comment='寄存时的状态，0表示已开瓶，1表示未开瓶')
    deposit_person = db.Column(db.String(64), db.ForeignKey('customers.id'))
    deposit_confirm_waiter = db.Column(db.String(64), db.ForeignKey('business_unit_employees.id'))
    deposit_bu_id = db.Column(db.String(64), db.ForeignKey('business_units.id'), comment='存酒店铺')
    deposit_confirm_at = db.Column(db.DateTime, comment="服务员确认时间")
    pickup_waiter = db.Column(db.String(64), db.ForeignKey('business_unit_employees.id'))
    pickup_at = db.Column(db.DateTime, comment="取酒时间")
    create_at = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建时间即为客户寄存时间')
    delete_at = db.Column(db.DateTime, comment='取消寄存时间')


class Elements(db.Model):
    __tablename__ = 'elements'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    icon = db.Column(db.String(50))
    url = db.Column(db.String(250))
    order = db.Column(db.SmallInteger, default=0)
    bg_color = db.Column(db.String(50))
    type = db.Column(db.String(20))
    permission = db.Column(db.String(100), unique=True, index=True, comment='API接口权限')
    parent_id = db.Column(db.Integer, db.ForeignKey('elements.id'))
    parent = db.relationship('Elements', backref="children", remote_side=[id])

    def __repr__(self):
        return '<Element\'s name: %r>' % self.name


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


class PointRecords(db.Model):
    __tablename__ = 'point_records'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    source_type = db.Column(db.SmallInteger, default=1, comment='1: 订单, 提在字典表中，查询point_records获取')
    source_id = db.Column(db.String(64), comment='积分源ID')
    card_id = db.Column(db.String(64), db.ForeignKey('member_cards.id'))
    operation_type = db.Column(db.SmallInteger, default=1, comment='1: 增长， 2: 消费，3: 罚扣')
    points = db.Column(db.Integer, comment='积分数')
    note = db.Column(db.String(100), comment='预留给客服做备注')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)


class MemberCards(db.Model):
    """
    用户登陆小程序后，没有会员卡，获取邀请码之后，可升级为代理商，分别为1级和2级，通过member_type来区分.
    grade来区分登记，1表示一级， 2表示二级。
    普通用户grade目前仅为1
    2020-07-22说明
    """
    __tablename__ = 'member_cards'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    card_no = db.Column(db.String(50), nullable=False, comment='会员卡号')
    member_type = db.Column(db.SmallInteger, default=0, comment='会员类型， 0为普通C端会员； 1 为代理商')
    balance = db.Column(db.DECIMAL(11, 2), default=0.00, comment='余额')
    customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    status = db.Column(db.SmallInteger, default=1, comment='会员卡状态 0: 禁用， 1：正常, 2：挂失')
    grade = db.Column(db.SmallInteger, default=1,
                      comment='会员卡等级，在OptionsDict表中查找card_grades来获取对应的文字描述.默认为1')
    discount = db.Column(db.DECIMAL(3, 2), default=1.00, comment="会员折扣")
    shop_id = db.Column(db.String(64), default='all', comment='预留，对于店铺发店铺会员卡，目前会员卡为商城全局')
    open_date = db.Column(db.DateTime, default=datetime.datetime.now, comment="开卡日期")
    validate_date = db.Column(db.DateTime, comment="卡有效期")
    note = db.Column(db.String(100), comment='备注')
    creator_id = db.Column(db.String(64), db.ForeignKey('users.id'))
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime, comment='如果不为空，则表示软删除')
    recharge_records = db.relationship('MemberRechargeRecords', backref='card', uselist=False)

    def __repr__(self):
        return '<Member card no %r>' % self.card_no


class MemberPolicies(db.Model):
    """加入会员的策略，包括充值多少送多少，送多少积分，送多少优惠券"""
    __tablename__ = 'member_policies'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(100), index=True, comment='策略名称')
    to_type = db.Column(db.SmallInteger, default=0, comment='0, 直客；1， 代理；2， 区域总代')
    to_level = db.Column(db.SmallInteger, default=1, comment='直客， 1级最小； 代理（总代），1级最大')
    recharge_amount = db.Column(db.DECIMAL(11, 2), index=True, default=0.00, comment='充值金额')
    present_amount = db.Column(db.DECIMAL(11, 2), index=True, default=0.00, comment='赠送金额')
    bounce_scores = db.Column(db.Integer, default=0, comment='奖励积分')
    bounce_coupons = db.relationship(
        'Coupons',
        secondary=member_policy_bounce_coupons,
        backref=db.backref(
            'member_bounce_policies'
        )
    )
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<Member card policy name %r>' % self.name


class MemberRechargeRecords(db.Model):
    """会员充值记录"""
    __tablename__ = 'member_recharge_records'
    id = db.Column(db.String(64), primary_key=True, default=make_order_id)
    recharge_amount = db.Column(db.DECIMAL(9, 2), default=0.00, comment="充值金额")
    member_card = db.Column(db.String(64), db.ForeignKey('member_cards.id'))
    note = db.Column(db.String(200), comment='备注')
    is_pay = db.Column(db.SmallInteger, default=0, index=True, comment="默认0. 0：未支付， 1：完成支付， 2：支付失败, 3:支付中")
    pre_pay_time = db.Column(db.DateTime, default=datetime.datetime.now, comment='预支付时间')
    usable = db.Column(db.SmallInteger, default=1, comment='0 不可用， 1 可用；例如开通会员卡的金额可设置为不可使用')
    wechat_pay_result = db.relationship("WechatPay", backref='member_recharge_record', uselist=False)
    status = db.Column(db.SmallInteger, default=1, comment='0, 取消，1 正常')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<Member recharge record No. %r>' % self.id


class MemberCardConsumption(db.Model):
    """会员卡消费记录"""
    __tablename__ = 'member_card_consumption'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    consumption_sum = db.Column(db.DECIMAL(9, 2), default=0.00, comment='消费额')
    member_card_id = db.Column(db.String(64), db.ForeignKey('member_cards.id'))
    note = db.Column(db.String(200), comment='备注')
    shop_order_id = db.Column(db.String(64), db.ForeignKey("shop_orders.id"))
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return '<Member card consumption No. %r>' % self.id


class InvitationCode(db.Model):
    """
    邀请码。后台管理员生成邀请码，分配给一级代理商。一级代理商分配给二级的邀请码，也是由后台管理员生成分配给一级代理商
    """
    __tablename__ = 'invitation_code'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    tobe_type = db.Column(db.SmallInteger, comment='邀请后成为的类型，对应member_cards中的member_type')
    tobe_level = db.Column(db.SmallInteger, comment='邀请后成为的等级，对应member_cards中的grade')
    code = db.Column(db.String(64), unique=True, comment='邀请码')
    manager_customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'), comment='管理者ID')
    used_customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'), comment='使用者ID')
    interest_customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'), comment='利益关系ID')
    new_member_card_id = db.Column(db.String(64), db.ForeignKey('member_cards.id'), comment='开卡id')
    creator_id = db.Column(db.String(64), db.ForeignKey('users.id'))
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    validity_at = db.Column(db.DateTime)
    used_at = db.Column(db.DateTime, comment='如果不为空，则表示已经使用，软删除')


class SceneInvitation(db.Model):
    """
    场景邀请码，用于生成一个在一定时间范围内有效的邀请码（二维码）
    """
    __tablename__ = 'scene_invitation'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(100), comment='邀请码名称')
    tobe_type = db.Column(db.SmallInteger, comment='邀请后成为的类型，对应member_cards中的member_type')
    tobe_level = db.Column(db.SmallInteger, comment='邀请后成为的等级，对应member_cards中的grade')
    code = db.Column(db.String(64), unique=True, comment='邀请码')
    manager_customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'), comment='管理者ID')
    interest_customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'), comment='利益关系ID')
    invitees = db.relationship(
        'MemberCards',
        secondary=scene_member_cards,
        backref=db.backref(
            'scene_invitation_code'
        )
    )
    max_invitees = db.Column(db.Integer, default=0, comment='最大邀请数, 0表示不限制')
    start_at = db.Column(db.DateTime, comment='有效期开始时间')
    end_at = db.Column(db.DateTime, comment='有效期结束时间')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)


class Scores(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    reason = db.Column(db.String(64), comment='变更原因')
    quantity = db.Column(db.Integer, comment='积分数值')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class Customers(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    phone = db.Column(db.String(15), index=True)
    email = db.Column(db.String(64), index=True)
    openid = db.Column(db.String(64), index=True)
    unionid = db.Column(db.String(64), index=True)
    session_key = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), index=True)
    true_name = db.Column(db.String(30))
    purse = db.Column(db.DECIMAL(7, 2), default=0.00, comment='用户零钱包，用于存放返佣金额')
    level = db.Column(db.SmallInteger, default=1, comment="用户等级")
    total_points = db.Column(db.Integer, default=0, comment="用户积分")
    total_consumption = db.Column(db.DECIMAL(7, 2), default=0.00, comment='累积消费')
    total_count = db.Column(db.Integer, default=0, comment='累积消费次数')
    role_id = db.Column(db.Integer, db.ForeignKey('customer_roles.id'))
    # 0 unknown, 1 male, 2 female
    gender = db.Column(db.SmallInteger)
    birthday = db.Column(db.Date)
    status = db.Column(db.SmallInteger, comment='1: 正常 0: 删除', default=1)
    address = db.Column(db.String(200))
    login_info = db.relationship('LoginInfo', backref='login_customer', lazy='dynamic')
    orders = db.relationship("ShopOrders", backref='consumer', lazy='dynamic')
    item_orders = db.relationship("ItemsOrders", backref='consumer', foreign_keys='ItemsOrders.customer_id', lazy='dynamic')
    success_item_orders = db.relationship("ItemsOrders", backref='salesman', foreign_keys='ItemsOrders.salesman_id', lazy='dynamic')
    profile_photo = db.Column(db.String(200), comment='微信头像url')
    first_order_table = db.Column(db.String(20), index=True, default="ShopOrders", comment='首单对应表格类名称')
    first_order_id = db.Column(db.String(64), index=True, comment='对应first_order_table表的id，用于确认用户首单，但不局限是哪个业务的首单')
    express_addresses = db.relationship("ExpressAddress", backref='item_sender', lazy='dynamic')
    coupons = db.relationship('CouponReady', backref='receiptor', lazy='dynamic')
    member_card = db.relationship('MemberCards', backref='card_owner', foreign_keys='MemberCards.customer_id',
                                  lazy='dynamic')
    wechat_purse_transfer = db.relationship('WechatPurseTransfer', backref='purse_owner', uselist=False)
    parent_id = db.Column(db.String(64), db.ForeignKey('customers.id'), comment="邀请者，分享小程序入口之后的级联关系写在parent中")
    parent = db.relationship('Customers', backref="children", foreign_keys='Customers.parent_id', remote_side=[id])

    invitor_id = db.Column(db.String(64), db.ForeignKey('customers.id'), comment="代理商邀请")
    invitor = db.relationship('Customers', backref="be_invited", foreign_keys='Customers.invitor_id', remote_side=[id])

    bu_id = db.Column(db.String(64), db.ForeignKey("business_units.id"), comment='所归属的店铺')
    bu_employee_id = db.Column(db.String(64), db.ForeignKey("business_unit_employees.id"), comment='邀请使用小程序的员工ID')

    interest_id = db.Column(db.String(64), db.ForeignKey('customers.id'), comment="利益关系")
    interest = db.relationship('Customers', backref="children_market", foreign_keys='Customers.interest_id',
                               remote_side=[id])

    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)

    invitation_manager = db.relationship('InvitationCode', backref='manager',
                                         foreign_keys='InvitationCode.manager_customer_id',
                                         lazy='dynamic')
    invitation_user = db.relationship('InvitationCode', backref='user',
                                      foreign_keys='InvitationCode.used_customer_id',
                                      lazy='dynamic')
    invitation_interested_user = db.relationship('InvitationCode', backref='interested_customer',
                                                 foreign_keys='InvitationCode.interest_customer_id',
                                                 lazy='dynamic')

    shopping_cart = db.relationship("ShoppingCart", backref='buyer', foreign_keys='ShoppingCart.customer_id',lazy='dynamic')
    sold_to_cart = db.relationship("ShoppingCart", backref='salesman', foreign_keys='ShoppingCart.salesman_id', lazy='dynamic')
    total_cargoes = db.relationship("TotalCargoes", backref='owner', lazy='dynamic')
    refund_orders = db.relationship("Refund", backref='aditor', lazy='dynamic')
    score_changes = db.relationship("Scores", backref='score_owner', lazy='dynamic')
    personal_rebates = db.relationship("PersonalRebates", backref='rebates_owner', lazy='dynamic')
    cloud_wine_personal_rebate_records = db.relationship("CloudWinePersonalRebateRecords", backref='rebate_owner',
                                                         uselist=False)
    business_unit_employee = db.relationship('BusinessUnitEmployees', backref='employee_wechat', uselist=False,
                                             foreign_keys='BusinessUnitEmployees.customer_id')
    franchisee_operator = db.relationship('FranchiseeOperators', backref='employee_wechat', uselist=False)
    confirmed_express_orders = db.relationship('CloudWineExpressOrders', backref='express_confirmer', lazy='dynamic',
                                               foreign_keys='CloudWineExpressOrders.confirm_id')
    applied_express_orders = db.relationship('CloudWineExpressOrders', backref='express_applicant', lazy='dynamic',
                                             foreign_keys='CloudWineExpressOrders.apply_id')

    self_item_verification_orders = db.relationship('ItemVerification', backref='verify_applier', uselist=False,
                                                    foreign_keys='ItemVerification.customer_id')
    item_verification_bu_orders = db.relationship('ItemVerification', backref='item_verifier', uselist=False,
                                                  foreign_keys='ItemVerification.verification_customer_id')

    def __init__(self, **kwargs):
        super(Customers, self).__init__(**kwargs)
        if self.role is None:
            if self.phone == current_app.config['FLASKY_ADMIN']:
                self.role = CustomerRoles.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = CustomerRoles.query.filter_by(default=True).first()

    def verify_code(self, message):
        """
        验证码
        :param message:
        :return:
        """
        login_key = f"front::verification_code::{self.phone}"
        return True if redis_db.exists(login_key) and redis_db.get(login_key) == message else False

    def can(self, permissions):
        a = self.role is not None and (self.role.permissions & permissions) == permissions
        b = self.business_unit_employee is not None and (
                self.business_unit_employee.role.permissions & permissions) == permissions
        c = self.franchisee_operator is not None and (
                self.franchisee_operator.role.permissions & permissions) == permissions
        return a or b or c

    @property
    def grade(self):
        member_card = MemberCards.query.filter(MemberCards.customer_id.__eq__(self.id),
                                               MemberCards.member_type.__eq__(1), MemberCards.delete_at.__eq__(None),
                                               MemberCards.status.__eq__(1)).first()

        return member_card.grade if member_card else 0

    @property
    def member_type(self):
        member_card = MemberCards.query.filter(MemberCards.customer_id.__eq__(self.id),
                                               MemberCards.delete_at.__eq__(None),
                                               MemberCards.status.__eq__(1)).first()

        return member_card.member_type if member_card else 0

    @property
    def member_grade(self):
        member_card = MemberCards.query.filter(MemberCards.customer_id.__eq__(self.id),
                                               MemberCards.delete_at.__eq__(None),
                                               MemberCards.status.__eq__(1)).first()

        return member_card.grade if member_card else None

    @property
    def card(self):
        member_card = MemberCards.query.filter(MemberCards.customer_id.__eq__(self.id),
                                               MemberCards.delete_at.__eq__(None),
                                               MemberCards.status.__eq__(1)).first()

        return member_card

    @property
    def card_balance(self):
        member_card = MemberCards.query.filter(MemberCards.customer_id.__eq__(self.id),
                                               MemberCards.delete_at.__eq__(None),
                                               MemberCards.status.__eq__(1)).first()
        return member_card.balance if member_card else Decimal("0.00")

    def __repr__(self):
        return f"<Customers {self.openid}::{self.phone}>"


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    phone = db.Column(db.String(15), nullable=False, index=True)
    username = db.Column(db.String(64), index=True)
    email = db.Column(db.String(64), index=True)
    true_name = db.Column(db.String(30))
    birthday = db.Column(db.Date)
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
    address = db.Column(db.String(200))
    login_info = db.relationship('LoginInfo', backref='login_user', lazy='dynamic')
    member_card = db.relationship('MemberCards', backref='cards_creator', lazy='dynamic')
    invitation = db.relationship('InvitationCode', backref='creator', lazy='dynamic')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)

    @property
    def permissions(self):
        return Elements.query.outerjoin(roles_elements).outerjoin(Roles).outerjoin(user_role).outerjoin(Users). \
            filter(Users.id == self.id, Elements.permission is not None).order_by(Elements.order).all()

    @property
    def elements(self):
        return Elements.query.outerjoin(roles_elements).outerjoin(Roles).outerjoin(user_role).outerjoin(Users). \
            filter(
            Users.id == self.id,
            Elements.type != 'api'
        ).order_by(Elements.order).all()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def verify_code(self, message):
        """
        验证码
        :param message:
        :return:
        """
        login_key = f"back::verification_code::{self.phone}"
        return True if redis_db.exists(login_key) and redis_db.get(login_key) == message else False

    def __repr__(self):
        return '<User %r>' % self.username


class Countries(db.Model):
    __tablename__ = 'countries'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, index=True, nullable=False)
    longitude = db.Column(db.String(20))
    latitude = db.Column(db.String(20))
    population = db.Column(db.Integer)
    provinces = db.relationship("Provinces", backref="countries", lazy='dynamic')


class Provinces(db.Model):
    __tablename__ = 'provinces'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, index=True, nullable=False)
    longitude = db.Column(db.String(20))
    latitude = db.Column(db.String(20))
    population = db.Column(db.Integer)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'))
    cities = db.relationship("Cities", backref='provinces', lazy='dynamic')


class Cities(db.Model):
    __tablename__ = 'cities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, index=True, nullable=False)
    longitude = db.Column(db.String(20))
    latitude = db.Column(db.String(20))
    population = db.Column(db.Integer)
    province_id = db.Column(db.Integer, db.ForeignKey('provinces.id'))
    districts = db.relationship("Districts", backref='included_cities', lazy='dynamic')
    express_address = db.relationship("ExpressAddress", backref='buyer_cities', lazy='dynamic')


class Districts(db.Model):
    __tablename__ = 'districts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, index=True, nullable=False)
    longitude = db.Column(db.String(20))
    latitude = db.Column(db.String(20))
    population = db.Column(db.Integer)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'))
    express_address = db.relation("ExpressAddress", backref='buyer_district', lazy='dynamic')


class Brands(db.Model):
    __tablename__ = 'brands'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(100), nullable=False, index=True)
    logo = db.Column(db.String(64), db.ForeignKey('obj_storage.id'))
    company_name = db.Column(db.String(100))
    company_address = db.Column(db.String(100))
    spu = db.relationship('SPU', backref='brand', lazy='dynamic')


class Classifies(db.Model):
    __tablename__ = 'classifies'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(50), nullable=False)
    spu = db.relationship('SPU', backref='classifies', lazy='dynamic')


class Standards(db.Model):
    __tablename__ = 'standards'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(50), nullable=False, unique=True, index=True)
    values = db.relationship('StandardValue', backref='standards', lazy='dynamic')


class StandardValue(db.Model):
    __tablename__ = 'standard_value'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    standard_id = db.Column(db.String(64), db.ForeignKey('standards.id'))
    value = db.Column(db.String(50), nullable=False, unique=True, index=True)


class SPU(db.Model):
    __tablename__ = 'spu'
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
    objects = db.relationship(
        'ObjStorage',
        secondary=spu_obj,
        backref=db.backref('obj_spu')
    )
    brand_id = db.Column(db.String(64), db.ForeignKey('brands.id'))
    classify_id = db.Column(db.String(64), db.ForeignKey('classifies.id'))
    sku = db.relationship('SKU', backref='the_spu', lazy='dynamic')
    status = db.Column(db.SmallInteger, default=0, comment="1 上架； 0 下架")
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class PurchaseInfo(db.Model):
    __tablename__ = 'purchase_info'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    sku_id = db.Column(db.String(64), db.ForeignKey('sku.id'))
    amount = db.Column(db.Integer, comment='进货，出货数量')
    operator = db.Column(db.String(64))
    operator_at = db.Column(db.DateTime, comment="进货或者出货时间")
    express_order_id = db.Column(db.String(64), db.ForeignKey("cloudwine_express_orders.id"))
    express_to_id = db.Column(db.String(64), db.ForeignKey("franchisees.id"))
    franchisee_purchase_order = db.relationship("FranchiseePurchaseOrders", backref="original_order", uselist=False)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    status = db.Column(db.SmallInteger, default=1, comment="1 正常 0 作废")
    dispatch_status = db.Column(db.SmallInteger, default=0, comment="0 已发货未确认，1已发货并确认， 3 未发货")
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    memo = db.Column(db.String(200), comment="备忘，例如作废原因")


class WareHouse(db.Model):
    __tablename__ = 'warehouse'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(64))
    address = db.Column(db.String(100))
    purpose = db.Column(db.String(100), comment='仓库用途')
    status = db.Column(db.SmallInteger, default=1, comment='仓库状态，默认1为在用')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)
    total_cargoes = db.relationship("TotalCargoes", backref='cargo_warehous', lazy='dynamic')


class PackingItemOrders(db.Model):
    __tablename__ = 'packing_item_orders'
    # 当进入分装流程时，先生成一个分装的订单，如果
    id = db.Column(db.String(64), primary_key=True, default=make_order_id)
    total_cargoes_id = db.Column(db.String(64), db.ForeignKey('total_cargoes.id'))
    shop_order_id = db.Column(db.String(64), db.ForeignKey('shop_orders.id'), comment='分装的总订单')
    materials_in_cart = db.relationship('ShoppingCart', backref='packing_order', lazy='dynamic')
    consumption = db.Column(db.DECIMAL(7, 2), comment='总量中分装的消耗量，单位与total_cargoes中的unit相同')
    loss = db.Column(db.DECIMAL(7, 2), default=0.00, comment='分装过程的损耗，默认为0.00')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now, comment='创建分装的日期')
    # 支付时间看对应的订单
    packing_at = db.Column(db.String(64), comment='选择完所有材料后提交结算的时间')
    pay_at = db.Column(db.DateTime,
                       comment='支付完成回调时，如果是shop_orders中外键关联packing_order不为空，那么就update这个parcking_order中的pay_at，表示支付完成')
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    # 如果delete_at不为空，表示此分装订单没有生效
    delete_at = db.Column(db.DateTime)


class TotalCargoes(db.Model):
    __tablename__ = 'total_cargoes'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    cargo_code = db.Column(db.String(64), comment='货物编号')
    warehouse_id = db.Column(db.String(64), db.ForeignKey('warehouse.id'), comment='货物存储房间')
    cargo_pan = db.Column(db.String(3), comment='货物水平位置')
    cargo_tilt = db.Column(db.String(3), comment='货物垂直位置')
    cargo_zoom = db.Column(db.String(3), comment='货物焦距位置')
    order_id = db.Column(db.String(64), db.ForeignKey('shop_orders.id'), comment='外键关联订单')
    storage_date = db.Column(db.DateTime)
    init_total = db.Column(db.DECIMAL(7, 2), comment='初始的总量')
    last_total = db.Column(db.DECIMAL(7, 2), comment='最后的总量')
    unit = db.Column(db.String(10), default='斤', comment='货物单位')
    key_code = db.Column(db.String(100), comment='智能锁远程访问id')
    key_pwd = db.Column(db.String(100), comment='key 密钥')
    # 存放封坛相关的照片，后续还能上传
    cargo_media = db.relationship(
        'ObjStorage',
        secondary=cargo_obj,
        backref=db.backref('obj_cargo')
    )
    packing_orders = db.relationship('PackingItemOrders', backref='parent_cargo', lazy='dynamic')
    owner_name = db.Column(db.String(20), comment='货物主人姓名')
    owner_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class SkuMemberPrice(db.Model):
    __tablename__ = 'sku_member_price'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    sku_id = db.Column(db.String(64), db.ForeignKey('sku.id'))
    member_price = db.Column(db.DECIMAL(10, 2), default=0.00)
    customer_level = db.Column(db.SmallInteger, comment='Customers.level')
    start_price = db.Column(db.DECIMAL(11, 2), comment='区间开始价格')
    end_price = db.Column(db.DECIMAL(11, 2), comment='区间结束价格')
    start_bottle = db.Column(db.Integer, comment='购买瓶数区间开始')
    end_bottle = db.Column(db.Integer, comment='购买瓶数区间结束')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class SKU(db.Model):
    __tablename__ = 'sku'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(100), nullable=False, index=True)
    subtitle = db.Column(db.String(100), index=True, comment="显示在sku主标题下的描述文字")
    desc = db.Column(db.String(200), comment="商品标题下的描述，预留，目前无用")
    show_price = db.Column(db.String(13), default='0.00', comment='显示价格， 当special不为0时，显示此价格，并且用删除线')
    price = db.Column(db.DECIMAL(10, 2), default=0.00)
    seckill_price = db.Column(db.DECIMAL(10, 2), default=0.00, comment='当SKU参加秒杀活动时，设置秒杀价格写在这个字段，如果不为0， 则表示参加秒杀，查找秒杀活动')
    discount = db.Column(db.DECIMAL(3, 2), default=1.00)
    member_prices = db.relationship("SkuMemberPrice", backref="the_sku", lazy='dynamic')
    score_type = db.Column(db.SmallInteger, default=0, comment='是否可用积分')
    get_score = db.Column(db.Integer, comment="可以获得的积分")
    max_score = db.Column(db.Integer, comment='最多可用积分')
    contents = db.Column(db.Text(length=(2 ** 32) - 1), comment='富文本，sku描述')
    quantity = db.Column(db.Integer, default=0, index=True)
    spu_id = db.Column(db.String(64), db.ForeignKey('spu.id'))
    unit = db.Column(db.String(6), nullable=False)
    special = db.Column(db.SmallInteger, default=0,
                        comment="0 非特价商品，1 特价商品， 2 赠品，不可单独销售, 30 ~ 69: 表示有后续业务流程的商品，当前用31，表示分装所需包装材料，订单生成后，会产生分装订单")
    need_express = db.Column(db.SmallInteger, default=1, comment="1: 可快递， 0: 不可快递")
    express_fee = db.Column(db.DECIMAL(7, 2), default=10.00, comment='sku 默认快递费')
    per_user = db.Column(db.SmallInteger, default=0, comment="设置限购量，默认为0不限购，一般在特价，秒杀折扣时使用")
    values = db.relationship(
        'StandardValue',
        secondary=sku_standardvalue,
        backref=db.backref('sku')
    )
    objects = db.relationship(
        'ObjStorage',
        secondary=sku_obj,
        backref=db.backref('obj_sku')
    )
    rebates_id = db.Column(db.String(64), db.ForeignKey("rebates.id"))
    status = db.Column(db.SmallInteger, default=0, comment="1 上架； 0 下架")
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)
    could_get_coupon_id = db.Column(db.String(64), db.ForeignKey('coupons.id'), comment='如果是直客，那么可以设置获取优惠券')
    order = db.relationship(
        'ShopOrders',
        secondary=sku_shoporders,
        backref=db.backref('order_sku')
    )
    purchase_info = db.relationship('PurchaseInfo', backref='purchase_sku', lazy='dynamic')
    sku_layout = db.relationship('SKULayout', backref='layout_sku', lazy='dynamic')
    shopping_cart = db.relationship('ShoppingCart', backref='desire_sku', lazy='dynamic')
    sku_orders = db.relationship("ItemsOrders", backref='bought_sku', lazy='dynamic')
    franchisee_purchase_skus = db.relationship("FranchiseePurchaseOrders", backref='sku', lazy='dynamic')
    franchisee_inventory = db.relationship("FranchiseeInventory", backref='sku', lazy='dynamic')
    bu_inventory = db.relationship("BusinessUnitInventory", backref='sku', lazy='dynamic')
    bu_purchase_skus = db.relationship("BusinessPurchaseOrders", backref='sku', lazy='dynamic')
    deposits = db.relationship("Deposit", backref='sku', lazy='dynamic')
    cloudwine_express_orders = db.relationship("CloudWineExpressOrders", backref='sku', lazy='dynamic')
    fgps = db.relationship("FranchiseeGroupPurchase", backref='sku', lazy='dynamic')

    def member_price(self, customer_level):
        return SkuMemberPrice.query.filter(SkuMemberPrice.sku_id.__eq__(self.id),
                                           SkuMemberPrice.customer_level.__eq__(customer_level)).first().member_price


class PersonalRebates(db.Model):
    """
    个人返佣表。 支付成功后，吊起返佣计算流程
    """
    __tablename__ = 'personal_rebates'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    shop_order_id = db.Column(db.String(64), db.ForeignKey('shop_orders.id'))
    wechat_pay_id = db.Column(db.String(64), db.ForeignKey('wechat_pay.id'))
    customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    rebate = db.Column(db.DECIMAL(5, 2), comment='支付成功时该账户应得的返佣比例')
    rebate_value = db.Column(db.DECIMAL(9, 2), comment='返佣金额')
    score = db.Column(db.SmallInteger, default=0, comment='获赠的积分')
    status = db.Column(db.SmallInteger, default=0, comment='0: 不可提现（刚购买或者用户提出退货后） 1：可提现 2：已提现')
    # 创建日期过一定天数后才能提现
    relation = db.Column(db.String(40), comment='返佣关系')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class CloudWinePersonalRebateRecords(db.Model):
    """云酒窖版本个人返佣记录表"""
    __tablename__ = 'cloud_wine_personal_rebate_records'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    item_verification_id = db.Column(db.String(64), db.ForeignKey("item_verification.id"))
    rebate_customer_id = db.Column(db.String(64), db.ForeignKey("customers.id"))
    rebate_money = db.Column(db.DECIMAL(7, 2), index=True, comment='返佣的金额')
    rebate_score = db.Column(db.Integer, index=True, comment='返佣、奖励的金额')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class Rebates(db.Model):
    """
    invitor 指提供邀请码的用户，可以是公司市场部，也可以是一级代理。 邀请码都由后台统一生成
    parent 用来关联分享链接的上下级关系，用来锁定上下级；
    例如：
    1. 一级代理A 分享给未使用过商城的B， B成为商城的直客，成为A的下游，所有B的消费，A提成30%
    2. A某日说服B成为二级代理，A提供B升级邀请码，B成为二级后，A获取B销售额的10%
    3. B 某日想成为一级代理，A向总公司申请一级代理邀请码，分配给B，B的销售提成和A脱钩， A获取一次性费用3万元。此处预留，以后可能不脱钩，留1%的提成
    4. A的直客封坛，A返佣10%； B（二级）的用户或者自己封坛，B返佣10%， A也同样有销售额的10%提成（符合销售管理奖金10%的规则）
    5. B某日发展了用户C为二级， B提成C的销售额的5%， A也同样提成C的销售额的5% 。 C的提成政策按照二级代理计算
    6. C某日发展了用户D为二级， C提成D的销售额的5%， B没有提成，A提成D的销售额的5% 。
    7. B邀请C，C邀请D的邀请码，平台默认给每个二级代理10个二级代理邀请码
    8. B某日邀请用户E为一级， B或者E 直接咨询客户，客户联系对接E，进行沟通审核后分配一级代理邀请码 成功后B获取一次性佣金3万元
    9. 总部路演等方式，招的一级代理，或者二级代理，都挂在市场部账号下。市场部账号为一级代理。市场部拓展的渠道始终由市场部管理。
    10. 二级代理自己消费，或者其下游直客消费，提成20%， 封坛佣金10% 。
    11. 直客也可邀请用户成为二级或者一级，直接找自己上级或者客服咨询
    12. 关于邀请码的规则，一级代理商邀请码都由总部市场部发出； 二级邀请码，代理商都可以发，默认给10个，不够了找客服申请
    """
    __tablename__ = 'rebates'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(64), comment="用来命名返佣表名称")
    c_to_c_bonus_score = db.Column(db.DECIMAL(5, 2), comment='c to c 可获取的奖励积分, 这里的百分比是消费额的百分比作为积分, 从parent_id来查找')
    agent_second_rebate = db.Column(db.DECIMAL(5, 2), default=20.00, comment='填写百分比，譬如20.00, 表示返佣20%')
    agent_first_rebate = db.Column(db.DECIMAL(5, 2), default=30.00, comment='填写百分比，譬如30.00, 表示返佣30%')
    agent_second_invitor_rebate = db.Column(db.DECIMAL(5, 2), default=5.00, comment='填写百分比，譬如5.00, 表示返佣5%')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    sku = db.relationship("SKU", backref='rebate', lazy='dynamic')


class Coupons(db.Model):
    __tablename__ = 'coupons'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(64), nullable=False, comment="优惠券标题")
    desc = db.Column(db.String(100), comment='优惠券描述')
    icon = db.Column(db.String(64), db.ForeignKey('obj_storage.id'), comment="优惠券图标")
    quota = db.Column(db.Integer, default=1, comment='配额：发券数量')
    per_user = db.Column(db.SmallInteger, default=1, comment='每用户允许领取数量')
    take_count = db.Column(db.Integer, default=0, comment='已领取的优惠券数量')
    used_count = db.Column(db.Integer, default=0, comment='已使用的优惠券数量')
    valid_type = db.Column(db.SmallInteger, default=2, comment='时效:1绝对时效（领取后XXX-XXX时间段有效）  2相对时效（领取后N天有效）')
    valid_days = db.Column(db.Integer, default=1, comment='自领取之日起有效天数')
    absolute_date = db.Column(db.DateTime, comment='优惠券的绝对结束日期，当valid_type为1时，此项不能为空')
    status = db.Column(db.SmallInteger, comment='1生效 2失效 3已结束', default=1)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    coupon_sent = db.relationship("CouponReady", backref='coupon_setting', lazy='dynamic')
    promotion = db.relationship("Promotions", backref='coupon', uselist=False)
    coupon_for_sku = db.relationship("SKU", backref='could_get_coupon', uselist=False)


class CouponReady(db.Model):
    __tablename__ = 'coupon_ready'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    coupon_id = db.Column(db.String(64), db.ForeignKey('coupons.id'))
    status = db.Column(db.SmallInteger, default=1, comment="0: 作废，1：已领取未使用，2：已使用")
    order_id = db.Column(db.String(64), db.ForeignKey('shop_orders.id'))
    take_at = db.Column(db.DateTime, default=datetime.datetime.now)
    use_at = db.Column(db.DateTime)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    consumer = db.Column(db.String(64), db.ForeignKey('customers.id'))


class ShopOrders(db.Model):
    __tablename__ = 'shop_orders'
    id = db.Column(db.String(64), primary_key=True, default=make_order_id)
    customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    transaction_id = db.Column(db.String(64), comment="微信支付的订单号，回调中获取")
    items_total_price = db.Column(db.DECIMAL(10, 2), default=0.00, comment='未使用积分的总价')
    score_used = db.Column(db.Integer, default=0, comment="使用的积分")
    is_pay = db.Column(db.SmallInteger, default=0, comment="默认0. 0：未支付， 1：完成支付， 2：支付失败, 3:支付中")
    pay_err_code = db.Column(db.String(32), comment="微信支付回调结果，如果有错误")
    pay_err_code_des = db.Column(db.String(128), comment="微信支付回调结果描述")
    bank_type = db.Column(db.String(32), comment="回调用户的银行类型，如果成功")
    pre_pay_time = db.Column(db.DateTime, comment='后台支付获取预付ID成功时间')
    pay_time = db.Column(db.DateTime, comment="支付成功时间")
    cash_fee = db.Column(db.DECIMAL(10, 2), comment="微信支付实际现金支付金额")
    is_ship = db.Column(db.SmallInteger, default=0, comment="0：未发货，1：已发货")
    ship_time = db.Column(db.DateTime, comment="发货时间")
    receive_time = db.Column(db.DateTime, comment="收货时间")
    is_receipt = db.Column(db.SmallInteger, default=0, comment="0：未发货 1：已发货未签收 2：已发货已签收")
    need_express = db.Column(db.SmallInteger, default=0, comment="0, 不要快递，店铺取货；1， 快递发货")
    express_company = db.Column(db.String(50), comment='快递公司')
    express_number = db.Column(db.String(50), comment='快递号')
    express_fee = db.Column(db.DECIMAL(7, 2), default=0.00)
    express_address = db.Column(db.String(200), comment="记录下单时发货地址，防止地址记录修改。 原express_address表中address1+address2")
    express_postcode = db.Column(db.String(7), comment='邮编')
    express_recipient = db.Column(db.String(20), comment='收件人')
    express_recipient_phone = db.Column(db.String(13), comment='收件人手机号')
    status = db.Column(db.SmallInteger, default=1, comment="1：正常 2：禁用 0：订单取消(delete_at 写入时间)")
    items_orders_id = db.relationship("ItemsOrders", backref='shop_orders', lazy='dynamic')
    total_cargoes = db.relationship("TotalCargoes", backref='cargo_order', lazy='dynamic')
    packing_order = db.relationship("PackingItemOrders", backref='packing_item_order', lazy='dynamic')
    coupon_used = db.relationship("CouponReady", backref='order_using_coupon', uselist=False)
    message = db.Column(db.String(500), comment='用户留言')
    cancel_reason = db.Column(db.String(64), comment='取消原因，给用户下拉选择')
    invoice_type = db.Column(db.SmallInteger, default=0, comment="0: 个人 1: 企业")
    invoice_title = db.Column(db.String(100), comment='发票抬头，如果type是0，则此处为个人')
    invoice_tax_no = db.Column(db.String(20), comment='企业税号')
    inovice_email = db.Column(db.String(50), comment='发票发送邮箱')
    upgrade_level = db.Column(db.SmallInteger, comment='此订单若付款成功升级用户等级的数值')
    rebate_records = db.relationship('PersonalRebates', backref='related_order', lazy='dynamic')
    wechat_pay_result = db.relationship("WechatPay", backref='payed_order', uselist=False)
    card_consumption = db.relationship("MemberCardConsumption", backref='payed_by_card_order', uselist=False)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)

    @property
    def real_price(self):
        """扣除积分、优惠券、卡消费之后的真是价格"""
        if self.coupon_used:
            coupon_reduce = self.coupon_used.coupon_setting.promotion.benefits[0].reduced_amount
        else:
            coupon_reduce = Decimal("0.00")

        if self.card_consumption:
            card_reduce = self.card_consumption.consumption_sum
        else:
            card_reduce = Decimal("0.00")

        return self.items_total_price - self.score_used - coupon_reduce - card_reduce


class ItemsOrders(db.Model):
    __tablename__ = 'items_orders'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    order_id = db.Column(db.String(64), db.ForeignKey('shop_orders.id'))
    item_id = db.Column(db.String(64), db.ForeignKey('sku.id'))
    item_quantity = db.Column(db.Integer, default=1, index=True, comment='购买数量')
    verified_quantity = db.Column(db.Integer, default=0, index=True, comment='已核销的数量')
    item_price = db.Column(db.DECIMAL(10, 2), comment="下单时sku的价格，如果有show_price，记录show_price，否则记录price")
    transaction_price = db.Column(db.DECIMAL(10, 2), comment="实际交易的价格，未使用积分的价格，例如有会员价，有折扣（real_price）")
    customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    salesman_id = db.Column(db.String(64), db.ForeignKey('customers.id'),)
    customer_level = db.Column(db.SmallInteger, comment='用户购买时的等级，1，普通，2 代言人，3 达人。对应customer的level 1，2，3')
    benefits = db.relationship('Benefits', secondary=itemsorders_benefits, backref=db.backref('item_orders'))
    status = db.Column(db.SmallInteger, default=0, comment='1：正常 2：禁用 0：订单未完成 3:退货中，4: 退货成功')
    special = db.Column(db.SmallInteger, default=0, comment='0.默认正常商品；1.有仓储分装流程的商品')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)
    rates = db.Column(db.String(64), db.ForeignKey('evaluates.id'), comment='评分')
    refund_order = db.relationship("Refund", backref='item_order', uselist=False)
    verify_orders = db.relationship("ItemVerification", backref='item_order', lazy='dynamic')


class ItemVerification(db.Model):
    __tablename__ = "item_verification"
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    item_order_id = db.Column(db.String(64), db.ForeignKey('items_orders.id'))
    customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    verification_quantity = db.Column(db.Integer, default=1, index=True, comment="核销的数量")
    verification_customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    bu_id = db.Column(db.String(64), db.ForeignKey('business_units.id'))
    rebate_status = db.Column(db.SmallInteger, default=0, comment='0,未返佣，1，已返佣，2， 不可返佣')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class ExpressAddress(db.Model):
    """用于用户自己的收货地址"""
    __tablename__ = 'express_address'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    sender = db.Column(db.String(64), db.ForeignKey('customers.id'))
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), comment="目前不用，后续拆分地址后存放城市id")
    district = db.Column(db.Integer, db.ForeignKey('districts.id'), comment="目前不c用，后续拆分地址后存放区id")
    address1 = db.Column(db.String(100), comment="某某路xx号xx栋xx门牌号")
    address2 = db.Column(db.String(100))
    postcode = db.Column(db.String(10), comment="邮编")
    recipient = db.Column(db.String(50), comment="收件人")
    recipient_phone = db.Column(db.String(20), comment="收件人电话")
    status = db.Column(db.SmallInteger, default=1, comment="1：正常 0：删除")
    is_default = db.Column(db.Boolean, default=False)


class CloudWineExpressOrders(db.Model):
    """云酒窖发货单, 加盟商、店铺发货"""
    __tablename__ = 'cloudwine_express_orders'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    apply_id = db.Column(db.String(64), db.ForeignKey('customers.id'), comment='发货申请人id')
    send_unit_type = db.Column(db.String(20), index=True, comment='Franchisee, BusinessUnit')
    send_unit_id = db.Column(db.String(64), index=True, comment='商业单位的id，Franchisees表、BusinessUnits表的id')
    sender = db.Column(db.String(50), index=True, comment='发货申请人姓名')
    sender_phone = db.Column(db.String(15), index=True, comment='发货申请人电话')
    sender_memo = db.Column(db.String(100), comment='发货人留言')
    recipient = db.Column(db.String(50), index=True, comment="收件人")
    recipient_phone = db.Column(db.String(20), index=True, comment="收件人电话")
    recipient_addr = db.Column(db.String(200), comment='收货人地址')
    is_purchase = db.Column(db.SmallInteger, comment='0 不是进货，1 进货')
    sku_id = db.Column(db.String(64), db.ForeignKey('sku.id'))
    quantity = db.Column(db.Integer, comment='发货数量')
    apply_at = db.Column(db.DateTime, comment="申请发货时间")
    # 是否要公司二次确认？目前不需要
    franchisee_id = db.Column(db.String(64), db.ForeignKey('franchisees.id'), comment='此快递订单归属的加盟商ID')
    confirm_status = db.Column(db.SmallInteger, default=0, index=True, comment='2 拒绝，1 同意, 0 未确认')
    confirm_reason = db.Column(db.String(128), comment='审核的原因')
    confirm_id = db.Column(db.String(64), db.ForeignKey('customers.id'), comment='当申请人是BU，或者是加盟商运营人员时，需要加盟商老板确认')
    confirm_at = db.Column(db.DateTime, comment='确认可发货日期')
    express_company = db.Column(db.String(50), index=True, comment='快递公司，例如安能物流，顺丰快递')
    express_num = db.Column(db.String(100), comment='快递单号')
    is_sent = db.Column(db.SmallInteger, default=0, comment="1: 已发出， 2：未发出")
    send_at = db.Column(db.DateTime, comment='发货日期')
    is_received = db.Column(db.SmallInteger, default=0, comment="0: 未收到，1:已收到")
    received_at = db.Column(db.DateTime, comment="收到日期")
    purchase_order = db.relationship("PurchaseInfo", backref='express_order', uselist=False)
    franchisee_purchase_order = db.relationship("FranchiseePurchaseOrders", backref='express_order', uselist=False)
    bu_purchase_order = db.relationship("BusinessPurchaseOrders", backref='express_order', uselist=False)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class CloudWineExpressAddress(db.Model):
    """云酒窖发货地址表"""
    __tablename__ = 'cloudwine_express_address'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), comment="目前不用，后续拆分地址后存放城市id")
    district = db.Column(db.Integer, db.ForeignKey('districts.id'), comment="目前不用，后续拆分地址后存放区id")
    address1 = db.Column(db.String(100), comment="某某路xx号xx栋xx门牌号")
    address2 = db.Column(db.String(100))
    postcode = db.Column(db.String(10), comment="邮编")
    recipient = db.Column(db.String(50), index=True, comment="收件人")
    recipient_phone = db.Column(db.String(20), index=True, comment="收件人电话")
    status = db.Column(db.SmallInteger, default=1, index=True, comment="1：正常 0：删除")


class Evaluates(db.Model):
    __tablename__ = 'evaluates'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    express_rate = db.Column(db.SmallInteger, default=10, comment="物流评价0~10")
    item_rate = db.Column(db.SmallInteger, default=10, comment="商品评价0~10")
    content = db.Column(db.Text(length=(2 ** 32) - 1))
    used_pic = db.Column(db.String(64), db.ForeignKey('obj_storage.id'))
    item_order = db.relationship('ItemsOrders', backref='evaluates', lazy='dynamic')


class Layout(db.Model):
    __tablename__ = 'layout'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, comment="页面板块名称")
    desc = db.Column(db.String(100), comment="描述、备注")
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    layout_sku = db.relationship('SKULayout', backref='layout', lazy='dynamic')


class SKULayout(db.Model):
    __tablename__ = 'sku_layout'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    layout_id = db.Column(db.Integer, db.ForeignKey('layout.id'))
    sku_id = db.Column(db.String(64), db.ForeignKey('sku.id'), nullable=False)
    order = db.Column(db.Integer, default=1, comment="排序")
    status = db.Column(db.SmallInteger, default=1, comment='0 禁用 1 正常')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)


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


class PromotionGroups(db.Model):
    """设置促销活动组"""
    __tablename__ = 'promotion_groups'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    group_id = db.Column(db.SmallInteger, comment="组ID， 0 为特殊组，特殊组和任何组不互斥")
    priority = db.Column(db.SmallInteger, unique=True, comment="优先级不可重复，用于排序")
    name = db.Column(db.String(30))
    desc = db.Column(db.String(100))
    promotions = db.relationship('Promotions', backref='groups', lazy='dynamic')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)


class Gifts(db.Model):
    """折扣商品或者赠品表"""
    __tablename__ = 'gifts'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    sku = db.Column(db.String(64), db.ForeignKey('sku.id'))
    discount = db.Column(db.DECIMAL(3, 2), default=0.00, comment='如果是0折，则为赠送，其它折扣，则为降价商品')
    benefit = db.Column(db.String(64), db.ForeignKey('benefits.id'))
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)


class Benefits(db.Model):
    """活动利益表"""
    __tablename__ = 'benefits'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(64))
    with_amount = db.Column(db.Integer, default=0, comment="满多少金额")
    reduced_amount = db.Column(db.Integer, default=0, comment="满xx后减多少钱，只能是整数")
    discount_amount = db.Column(db.DECIMAL(3, 2), default=1.00, comment='满xx后的折扣')
    with_quantity = db.Column(db.Integer, default=0, comment="满多少件")
    free_quantity = db.Column(db.SmallInteger, default=0, comment="满xx送几件")
    pay_more = db.Column(db.DECIMAL(10, 2), default=0.00, comment='加价购，可选范围在gifts中，由pay_more_quantity来控制加价购可选商品数量')
    pay_more_quantity = db.Column(db.SmallInteger, comment='控制加价购数量')
    combo_price = db.Column(db.DECIMAL(10, 2), default=0.00, comment='仅当活动类型是4时生效, 添加的sku为活动范围，添加的gifts为这个sku套餐的其它sku')
    combo_express_fee = db.Column(db.DECIMAL(7, 2), default=0.00, comment='套餐的快递价格，例如药酒封坛，则为0')
    presell_price = db.Column(db.DECIMAL(10, 2), default=0.00, comment='当类型是5时， 设置预售定金')
    presell_multiple = db.Column(db.DECIMAL(3, 2), default=0.00, comment='预售定金倍数，例如定金是10元，倍数是1.5，那么抵扣商品15元')
    gifts = db.relationship('Gifts', secondary=benefits_gifts, backref=db.backref('benefits'))
    status = db.Column(db.SmallInteger, comment='1生效 2失效 3已结束', default=1)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    shopping_cart = db.relationship("ShoppingCart", backref='combo_benefit', lazy='dynamic')


class Promotions(db.Model):
    """
    用于设置活动规则
    """
    __tablename__ = 'promotions'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(64), comment="促销活动名称", unique=True, index=True)
    first_order = db.Column(db.SmallInteger, default=0, comment='0: 不是首单，1: 首单, 用户首单参加活动')
    reject_coupon = db.Column(db.SmallInteger, default=0, comment='是否排斥优惠券，默认0不排斥，1排斥')
    reject_score = db.Column(db.SmallInteger, default=0, comment='是否排斥积分，默认0不排斥，1排斥')
    customer_level = db.Column(db.SmallInteger, default=1, comment='用户等级，1为最低')
    gender = db.Column(db.SmallInteger, default=0, comment='参与的性别，默认为0， 1为男性、2为女性')
    age_min = db.Column(db.SmallInteger, default=0, comment='参与最小年龄，默认为0')
    age_max = db.Column(db.SmallInteger, default=200, comment='参与最大年龄，默认为200')
    promotion_type = db.Column(db.SmallInteger, comment='0: 满减，1：满赠，2：满折，3：加价购，4：套餐，5：预售, 6：秒杀, 7: 满减优惠券, 8: 满赠优惠券')

    express_free = db.Column(db.SmallInteger, default=0, comment="0: 不包邮, 1: 包邮")

    accumulation = db.Column(db.SmallInteger, default=0, comment='是否允许累积，默认为0，不允许。如果允许累加则为1。如果可以累加，则利益规则数量会大于')
    scope = db.Column(db.SmallInteger, default=1, comment='0：非全场，1: 全场， 2：线下')

    # 多对多关系
    brands = db.relationship('Brands', secondary=promotions_brands, backref=db.backref('brand_promotions'))
    spu = db.relationship('SPU', secondary=promotions_spu, backref=db.backref('spu_promotions'))
    sku = db.relationship('SKU', secondary=promotions_sku, backref=db.backref('sku_promotions'))
    classifies = db.relationship('Classifies',
                                 secondary=promotions_classifies,
                                 backref=db.backref('classifies_promotions'))
    benefits = db.relationship('Benefits', secondary=promotions_benefits, backref=db.backref('benefits_promotions'))
    group = db.Column(db.String(64), db.ForeignKey('promotion_groups.id'), comment='group_id 为-1表示是发优惠券，>=0的group，为活动')

    with_special = db.Column(db.SmallInteger, default=0, comment="1: 可用于特价商品 0: 不能。默认不能(商品优惠卷除外)")
    start_time = db.Column(db.DateTime, comment='活动开始时间')
    end_time = db.Column(db.DateTime, comment='活动结束时间')
    status = db.Column(db.SmallInteger, comment='1生效 2失效 3已结束', default=1)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    coupon_id = db.Column(db.String(64), db.ForeignKey('coupons.id'))

    def __repr__(self):
        return '<Promotion name %r>' % self.name


class Banners(db.Model):
    """
    Banners内容存储
    """
    __tablename__ = 'banners'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(64), index=True, nullable=False, comment="banner的名称")
    scene = db.Column(db.String(64), index=True, comment="banner所在页，空值为商城")
    order = db.Column(db.SmallInteger, default=0, comment="排序，若相同则无序")
    objects = db.Column(db.String(64), db.ForeignKey('obj_storage.id'))
    url = db.Column(db.String(200), comment="用于存放点击后跳转的链接")
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)


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


class ShoppingCart(db.Model):
    """
    用户购物车，用于存放用户的购物车清单，只存放sku的快照，图片，价格。若实际SKU删除（软删除）或者下架，则前端页面显示此商品已失效
    """
    __tablename__ = 'shopping_cart'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    sku_id = db.Column(db.String(64), db.ForeignKey('sku.id'))
    quantity = db.Column(db.SmallInteger, default=1, comment="购买的数量")
    combo = db.Column(db.String(64), db.ForeignKey('benefits.id'),
                      comment='前端页面选择的combo，实质为这个套餐中的一种，为benefits表的id')
    status = db.Column(db.SmallInteger, default=1, comment='预留，默认为1，则显示在购物车中，如果为0， 则作为想买货物，不在购物车内')
    can_change = db.Column(db.SmallInteger, default=1, comment='1: 默认可改变；2: 不可改变')
    packing_item_order = db.Column(db.String(64), db.ForeignKey('packing_item_orders.id'))
    fgp_id = db.Column(db.String(64), db.ForeignKey('franchisee_group_purchase.id'))
    salesman_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class NewsSections(db.Model):
    """
    新闻栏目
    """
    __tablename__ = 'news_sections'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(64))
    section_image = db.Column(db.String(64), db.ForeignKey('obj_storage.id'))
    order = db.Column(db.SmallInteger, default=0, comment='栏目排序')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)
    news = db.relationship('NewsCenter', backref='news_section', lazy='dynamic')


class NewsCenter(db.Model):
    """
    咨询类
    """
    __tablename__ = 'news_center'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    title = db.Column(db.String(30), comment="主标题")
    sub_title = db.Column(db.String(30), comment="副标题")
    cover_image = db.Column(db.String(64), db.ForeignKey('obj_storage.id'))
    content = db.Column(db.Text(length=(2 ** 32) - 1), comment='富文本，sku描述')
    order = db.Column(db.SmallInteger, default=0, comment='文章排序')
    news_section_id = db.Column(db.String(64), db.ForeignKey('news_sections.id'))
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class Refund(db.Model):
    """
    退货申请单
    """
    __tablename__ = 'refund'
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    refund_quantity = db.Column(db.SmallInteger, comment='退货数量')
    refund_reason = db.Column(db.String(64), comment='退货原因')
    refund_desc = db.Column(db.String(200), comment='问题描述')
    collect_addr = db.Column(db.String(200), comment='取件地址')
    status = db.Column(db.SmallInteger, default=0, comment='0: 审核中，1: 审核成功，2：审核失败')
    audit_result = db.Column(db.String(200), comment="审核结果描述")
    auditor = db.Column(db.String(64), db.ForeignKey('customers.id'))
    express_no = db.Column(db.String(100), comment='快递单号')
    item_order_id = db.Column(db.String(64), db.ForeignKey('items_orders.id'))
    images = db.relationship(
        'ObjStorage',
        secondary=refund_images,
        backref=db.backref('refunds')
    )
    refund_id = db.Column(db.String(32), comment='微信退款单号')
    refund_fee = db.Column(db.Integer, comment='退款总金额,单位为分,可以做部分退款')
    cash_refund_fee = db.Column(db.Integer, comment='现金退款金额，单位为分，只能为整数')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class NewCustomerAwards(db.Model):
    """
    新注册用户奖励
    """
    __tablename__ = "new_customer_awards"
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.SmallInteger, default=0, comment='新用户奖励积分')
    could_get_coupons = db.relationship(
        'Coupons',
        secondary=new_customer_awards_coupons,
        backref=db.backref('new_customers')
    )
    share_award = db.Column(db.SmallInteger, default=0, comment='分享者可获取积分，分享者需要是直客，代理不能获取')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class Advertisements(db.Model):
    """
    页面广告
    """
    __tablename__ = "advertisements"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True, comment='广告名称')
    position = db.Column(db.String(50), index=True, comment='广告位置')
    image = db.Column(db.String(64), db.ForeignKey('obj_storage.id'))
    jump_to = db.Column(db.String(200), comment='跳转链接')
    start_at = db.Column(db.DateTime, default=datetime.datetime.now, comment="广告开始时间")
    end_at = db.Column(db.DateTime, comment="广告结束时间, 如果为空，则表示永久有效")
    wide = db.Column(db.Integer, comment='广告宽度')
    height = db.Column(db.Integer, comment='广告高度')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class WechatPay(db.Model):
    """微信支付订单"""
    __tablename__ = "wechat_pay"
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    prepay_id = db.Column(db.String(64), index=True, comment='预支付交易会话标识')
    prepay_at = db.Column(db.DateTime, default=datetime.datetime.now, comment='预支付时间')
    callback_err_code = db.Column(db.String(32), comment='错误代码')
    callback_err_code_des = db.Column(db.String(128), comment='错误代码描述')
    openid = db.Column(db.String(128), comment='用户openid')
    is_subscribe = db.Column(db.String(1), comment='是否关注公众账号')
    trade_type = db.Column(db.String(16), default='JSAPI', comment='交易类型')
    bank_type = db.Column(db.String(32), comment='付款银行')
    total_fee = db.Column(db.DECIMAL(11, 2), index=True, comment='订单总金额，单位为分')
    settlement_total_fee = db.Column(db.Integer, comment='应结订单金额=订单金额-非充值代金券金额，应结订单金额<=订单金额')
    fee_type = db.Column(db.String(8), default='CNY', comment='货币类型')
    cash_fee = db.Column(db.DECIMAL(11, 2), index=True, comment='现金支付金额订单现金支付金额，详见支付金额')
    cash_fee_type = db.Column(db.String(16), default='CNY', comment='现金支付货币类型')
    transaction_id = db.Column(db.String(32), index=True, comment='微信支付订单号')
    device_info = db.Column(db.String(32), index=True, comment='ShopOrder, MemberRecharge')
    attach = db.Column(db.String(128), index=True, comment='not in use')
    time_end = db.Column(db.DateTime, comment='支付完成时间')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)

    shop_order_id = db.Column(db.String(64), db.ForeignKey("shop_orders.id"))
    member_recharge_record_id = db.Column(db.String(64), db.ForeignKey("member_recharge_records.id"))
    rebates = db.relationship('PersonalRebates', backref='wechat_pay_order', uselist=False)


class WechatPurseTransfer(db.Model):
    """企业微信转零钱订单表"""
    __tablename__ = "wechat_purse_transfer"
    id = db.Column(db.String(64), primary_key=True, default=make_order_id, comment='partner_trade_no')
    customer_id = db.Column(db.String(64), db.ForeignKey('customers.id'))
    original_amount = db.Column(db.DECIMAL(11, 2), index=True, comment='提现时原始金额')
    amount = db.Column(db.DECIMAL(11, 2), index=True, comment='提现金额')
    desc = db.Column(db.String(100), comment='订单描述')
    result_code = db.Column(db.String(16), index=True,
                            comment="""SUCCESS/FAIL，注意：当状态为FAIL时，存在业务结果未明确的情况。
                            如果状态为FAIL，请务必关注错误代码（err_code字段），通过查询接口确认此次付款的结果。""")
    err_code = db.Column(db.String(32), index=True,
                         comment="""错误码信息，注意：出现未明确的错误码时（SYSTEMERROR等），
                         请务必用原商户订单号重试，或通过查询接口确认此次付款的结果。""")
    err_code_des = db.Column(db.String(128))
    payment_no = db.Column(db.String(64), index=True, comment="企业付款成功，返回的微信付款单号")
    payment_time = db.Column(db.DateTime, index=True, comment="企业付款成功时间, 格式2015-05-19 15:26:59")
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class CloudWineRebates(db.Model):
    """云酒窖返佣表"""
    __tablename__ = "cloud_wine_rebates"
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(50), index=True, comment="返佣名称")
    sku_id = db.Column(db.String(64), index=True, comment='sku_id')
    role_id = db.Column(db.Integer, db.ForeignKey('customer_roles.id'), comment='职业级别')
    consumer_level = db.Column(db.SmallInteger, comment='用户级别，customers.level')
    scene = db.Column(db.String(50), comment='业务场景，目前有PURCHASE; PICKUP')
    rebate = db.Column(db.DECIMAL(11, 2), index=True, comment='返佣金额')
    score = db.Column(db.Integer, index=True, comment='积分奖励')
    status = db.Column(db.SmallInteger, default=1)
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)


class FranchiseeGroupPurchase(db.Model):
    """加盟商直营团购表"""
    __tablename__ = "franchisee_group_purchase"
    id = db.Column(db.String(64), primary_key=True, default=make_uuid)
    name = db.Column(db.String(50), index=True, comment="团购名称")
    desc = db.Column(db.String(200), comment="描述")
    franchisee_id = db.Column(db.String(64), db.ForeignKey('franchisees.id'), comment='加盟商ID，可为空，如果不为空则该条团购为指定加盟商可用')
    sku_id = db.Column(db.String(64), db.ForeignKey('sku.id'), comment='sku_id')
    price = db.Column(db.DECIMAL(11, 2), index=True, comment="团购价")
    upgrade_level = db.Column(db.SmallInteger, default=0, comment='团购后升级到的级别，默认为0，不升级')
    amount = db.Column(db.Integer, comment="团购数量")
    status = db.Column(db.SmallInteger, default=1, comment='0, 无效；1，有效')
    create_at = db.Column(db.DateTime, default=datetime.datetime.now)
    update_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)
    delete_at = db.Column(db.DateTime)

    shopping_cart_records = db.relationship('ShoppingCart', backref='fgp', uselist=False)


aes_key = 'koiosr2d2c3p0000'

RECHARGE_REBATE_POLICY = 3

FIRST_PAGE_POPUP_URL = "IMAGE"

PermissionIP = redis_db.lrange('permission_ip', 0, -1)

PATH_PREFIX = os.path.abspath(os.path.dirname(__file__))

CERT_PATH = PATH_PREFIX + '/cert/apiclient_cert.pem'

KEY_PATH = PATH_PREFIX + '/cert/apiclient_key.pem'

CONFIG_FILE_PATH = PATH_PREFIX + 'config_file/'

CACTI_PIC_FOLDER = PATH_PREFIX + '/static/cacti_pic/'

MailTemplate_Path_Tmp = os.path.join(PATH_PREFIX, 'mail_template/tmp')

MailTemplate_Path = os.path.join(PATH_PREFIX, 'mail_template')

UploadFile_Path_Tmp = os.path.join(PATH_PREFIX, 'upload_file/tmp')

UploadFile_Path = os.path.join(PATH_PREFIX, 'upload_file')

MailResult_Path = os.path.join(PATH_PREFIX, 'mail_result')

QRCode_PATH = os.path.join(PATH_PREFIX, 'qrcode_image')

Temp_File_Path = os.path.join(PATH_PREFIX, 'tmp')

REQUEST_RETRY_TIMES = 1
REQUEST_RETRY_TIMES_PER_TIME = 1

# 支付成功后，7天内可退货
RETURN_IN_DAYS = 7
# 在过了退货期之后+3天可提现
REBATE_TO_CASH = 3

NEW_ONE_SCORES = 0
SHARE_AWARD = 0

RETRY_ERR_CODE = ["NOTENOUGH", "SYSTEMERROR", "NAME_MISMATCH", "SIGN_ERROR", "FREQ_LIMIT", "MONEY_LIMIT", "CA_ERROR",
                  "PARAM_IS_NOT_UTF8", "SENDNUM_LIMIT"]

CUSTOMER_L1_CONSUMPTION = Decimal("1197000000.00")

CUSTOMER_L2_CONSUMPTION = Decimal("2000000000.00")

REDIS_LONG_EXPIRE = 1800
REDIS_24H = 86400
REDIS_SHORT_EXPIRE = 300
