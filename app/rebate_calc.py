from app.models import ItemsOrders, ShopOrders, Customers, BusinessUnits, BusinessUnitEmployees, CustomerRoles, \
    ItemVerification, CloudWineRebates, make_uuid, FranchiseeOperators
from decimal import Decimal
from app.common import submit_return, false_return, success_return
from app.public_method import new_data_obj
from app import db


def get_rebate(role_name, sku_id, level, scene, amount):
    role_id = CustomerRoles.query.filter_by(name=role_name).first().id
    rebates = CloudWineRebates.query.filter(CloudWineRebates.role_id.__eq__(role_id),
                                            CloudWineRebates.sku_id.__eq__(sku_id),
                                            CloudWineRebates.consumer_level.__eq__(level),
                                            CloudWineRebates.scene.__eq__(scene),
                                            CloudWineRebates.status.__eq__(1),
                                            CloudWineRebates.delete_at.__eq__(None)).all()
    return Decimal("0.00") if rebates is None else sum(v.rebate for v in rebates) * Decimal(str(amount))


def bu_rebate(employee, waiter_rebate, operator_rebate, manager_rebate):
    pk_rebate = Decimal("0.00")
    if employee.role.name == "BU_WAITER":
        pk_rebate = waiter_rebate
    elif employee.role.name == "BU_OPERATOR":
        pk_rebate = waiter_rebate + operator_rebate
    elif employee.role.name == "BU_MANAGER":
        pk_rebate = waiter_rebate + operator_rebate + manager_rebate
    return pk_rebate


def purchase_rebate(consumer_id, item_verification_id):
    """
    购买场景的返佣
    :param consumer_id:
    :param item_verification_id:
    :return:
    """
    consumer_obj = Customers.query.get(consumer_id)
    bu_obj = consumer_obj.business_unit_employee.business_unit
    franchisee_obj = bu_obj.franchisee
    franchisee_manager = franchisee_obj.operators.filter(
        FranchiseeOperators.job_desc.__eq__(
            CustomerRoles.query.filter_by(name='FRANCHISEE_MANAGER').first().id)).first()
    item_verification_obj = ItemVerification.query.get(item_verification_id)
    item_order_id = item_verification_obj.item_order_id
    item_obj = ItemsOrders.query.get(item_order_id)
    shop_order_obj = item_obj.shop_orders
    sku_id = ItemsOrders.query.get(item_order_id).item_id
    if consumer_obj.first_order_table == shop_order_obj.__class__.__name__ and consumer_obj.first_order_id == shop_order_obj.id:
        # 表明当前item order 属于首单，调用 purchase_rebate来计算购买返佣
        scene = "FIRST_PURCHASE"
    else:
        scene = "PURCHASE"

    kwargs = {"sku_id": sku_id, "level": consumer_obj.level, "scene": scene}
    f_manager_rebate = get_rebate("FRANCHISEE_MANAGER", **kwargs)
    bu_manager_rebate = get_rebate("BU_MANAGER", **kwargs)
    bu_operator_rebate = get_rebate("BU_OPERATOR", **kwargs)
    bu_waiter_rebate = get_rebate("BU_WAITER", **kwargs)

    # 购买返回，返给加盟商老板
    franchisee_manager.employee_wechat.purse += f_manager_rebate
    new_data_obj("CloudWinePersonalRebateRecords", **{"id": make_uuid(),
                                                      "item_verification_id": item_verification_id,
                                                      "rebate_customer_id": franchisee_manager.employee_wechat.id,
                                                      "rebate_money": f_manager_rebate})

    bu_employees = consumer_obj.business_unit.employees

    operator_role_id = CustomerRoles.query.filter_by(name="BU_OPERATOR").first().id
    employee_operator = bu_employees.filter(BusinessUnitEmployees.job_desc.__eq__(operator_role_id)).first()
    manger_role_id = CustomerRoles.query.filter_by(name="BU_MANAGER").first().id
    employee_manager = bu_employees.filter(BusinessUnitEmployees.job_desc.__eq__(manger_role_id)).first()

    # 店铺卖酒返佣。老板有躺赚，服务员和店长只有在首单销售中会产生返佣
    consumer_obj.business_unit_employee.employee_wechat.purse += bu_waiter_rebate
    if bu_waiter_rebate > 0:
        new_data_obj("CloudWinePersonalRebateRecords", **{"id": make_uuid(),
                                                          "item_verification_id": item_verification_id,
                                                          "rebate_customer_id": bu_employees.employee_wechat.id,
                                                          "rebate_money": bu_waiter_rebate})
    if employee_operator and employee_operator.employee_wechat:
        employee_operator.employee_wechat.purse += bu_operator_rebate
        if bu_operator_rebate > 0:
            new_data_obj("CloudWinePersonalRebateRecords", **{"id": make_uuid(),
                                                              "item_verification_id": item_verification_id,
                                                              "rebate_customer_id": employee_operator.employee_wechat.id,
                                                              "rebate_money": bu_operator_rebate})
    if not employee_operator or not employee_operator.employee_wechat and (
            employee_manager and employee_manager.employee_wechat):
        employee_manager.employee_wechat.purse += bu_operator_rebate
        if bu_operator_rebate > 0:
            new_data_obj("CloudWinePersonalRebateRecords", **{"id": make_uuid(),
                                                              "item_verification_id": item_verification_id,
                                                              "rebate_customer_id": employee_manager.employee_wechat.id,
                                                              "rebate_money": bu_operator_rebate})
    if employee_manager and employee_manager.employee_wechat:
        employee_manager.employee_wechat.purse += bu_manager_rebate
        if bu_manager_rebate > 0:
            new_data_obj("CloudWinePersonalRebateRecords", **{"id": make_uuid(),
                                                              "item_verification_id": item_verification_id,
                                                              "rebate_customer_id": employee_manager.employee_wechat.id,
                                                              "rebate_money": bu_manager_rebate})
    item_verification_obj.rebate_status += 2

    return True


def pickup_rebate(item_verification_id, pickup_employee_id, consumer_id):
    """
    取酒场景触发的返佣。取酒场景，先判断订单是否为快递订单，如果是，则不能产生取酒返佣，且不能取酒。
    :param item_verification_id:
    :param pickup_employee_id:
    :param consumer_id:
    :return:
    """
    # first order rebate
    try:
        item_verification_obj = db.session.query(ItemVerification).with_for_update().filter(
            ItemVerification.id.__eq__(item_verification_id)).first()
        if item_verification_obj.rebate_status != 0:
            return false_return(message='此订单已经返佣'), 400

        item_order_id = item_verification_obj.item_order_id

        item_obj = ItemsOrders.query.get(item_order_id)

        consumer_obj = Customers.query.get(consumer_id)
        pickup_employee = BusinessUnitEmployees.query.get(pickup_employee_id)
        bu_obj = pickup_employee.business_unit
        franchisee_obj = bu_obj.franchisee
        franchisee_manager = franchisee_obj.operators.filter(
            FranchiseeOperators.job_desc.__eq__(
                CustomerRoles.query.filter_by(name='FRANCHISEE_MANAGER').first().id)).first()

        # 卖酒返佣，包括躺赚
        # purchase_rebate(consumer_id, item_verification_id)

        bu_employees = pickup_employee.business_unit.employees
        operator_role_id = CustomerRoles.query.filter_by(name="BU_OPERATOR").first().id
        employee_operator = bu_employees.filter(BusinessUnitEmployees.job_desc.__eq__(operator_role_id)).first()
        manger_role_id = CustomerRoles.query.filter_by(name="BU_MANAGER").first().id
        employee_manager = bu_employees.filter(BusinessUnitEmployees.job_desc.__eq__(manger_role_id)).first()

        # 获取rebate
        kwargs = {"sku_id": item_obj.item_id, "level": consumer_obj.level, "scene": "PICKUP",
                  "amount": item_verification_obj.verification_quantity}
        f_manager_rebate = get_rebate("FRANCHISEE_MANAGER", **kwargs)
        waiter_rebate = get_rebate("BU_WAITER", **kwargs)
        operator_rebate = get_rebate("BU_OPERATOR", **kwargs)
        manager_rebate = get_rebate("BU_MANAGER", **kwargs)

        # 取酒的时候，加盟商躺赚返佣计算
        franchisee_manager.employee_wechat.purse += f_manager_rebate
        new_data_obj("CloudWinePersonalRebateRecords", **{"id": make_uuid(),
                                                          "item_verification_id": item_verification_id,
                                                          "rebate_customer_id": franchisee_manager.employee_wechat.id,
                                                          "rebate_money": f_manager_rebate})

        # 店铺取酒返佣
        pickup_employee.employee_wechat.purse += waiter_rebate
        if waiter_rebate > 0:
            new_data_obj("CloudWinePersonalRebateRecords", **{"id": make_uuid(),
                                                              "item_verification_id": item_verification_id,
                                                              "rebate_customer_id": pickup_employee.employee_wechat.id,
                                                              "rebate_money": waiter_rebate})
        if employee_operator and employee_operator.employee_wechat:
            employee_operator.employee_wechat.purse += operator_rebate
            if operator_rebate > 0:
                new_data_obj("CloudWinePersonalRebateRecords", **{"id": make_uuid(),
                                                                  "item_verification_id": item_verification_id,
                                                                  "rebate_customer_id": employee_operator.employee_wechat.id,
                                                                  "rebate_money": operator_rebate})
        if not employee_operator or not employee_operator.employee_wechat and (
                employee_manager and employee_manager.employee_wechat):
            employee_manager.employee_wechat.purse += operator_rebate
            if operator_rebate > 0:
                new_data_obj("CloudWinePersonalRebateRecords", **{"id": make_uuid(),
                                                                  "item_verification_id": item_verification_id,
                                                                  "rebate_customer_id": employee_manager.employee_wechat.id,
                                                                  "rebate_money": operator_rebate})
        if employee_manager and employee_manager.employee_wechat:
            employee_manager.employee_wechat.purse += manager_rebate
            if manager_rebate > 0:
                new_data_obj("CloudWinePersonalRebateRecords", **{"id": make_uuid(),
                                                                  "item_verification_id": item_verification_id,
                                                                  "rebate_customer_id": employee_manager.employee_wechat.id,
                                                                  "rebate_money": manager_rebate})

        item_verification_obj.rebate_status += 1

        return submit_return("返佣成功", "返佣失败")
    except Exception as e:
        return false_return(message=str(e)), 400
