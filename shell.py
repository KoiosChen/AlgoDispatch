#!/usr/bin/env python
import os
from app import create_app, db
from app.models import Users, Roles, user_role, roles_elements, Elements, SKU, Layout, SKULayout, \
    Classifies, SPU, customer_role, Customers, Promotions, CustomerRoles, Brands, ShopOrders, ShoppingCart, \
    NewCustomerAwards, CouponReady, make_uuid
from app.public_method import query_coupon
from flask_script import Manager, Shell
from app.rebates.calc_rebate import calc
from flask_migrate import Migrate, MigrateCommand

__author__ = 'Koios'

app = create_app(os.getenv('FLASK_CONFIG') or 'production')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, Users=Users, Customers=Customers, ShoppingCart=ShoppingCart, query_coupon=query_coupon,
                CustomerRoles=CustomerRoles, Brands=Brands, SKU=SKU, ShopOrders=ShopOrders, Promotions=Promotions,
                NewCustomerAwards=NewCustomerAwards, CouponReady=CouponReady, make_uuid=make_uuid)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
