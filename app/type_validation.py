def type_base(parse_keys, value):
    required = [field for field, v in parse_keys.items() if v.get('required')]
    if isinstance(value, list):
        for el in value:
            if isinstance(el, dict):
                # 判断关键字
                if not set(required) & set(list(el.keys())):
                    lost_key = set(required) - set(list(el.keys()))
                    raise ValueError(f'缺少关键字{lost_key}')
                for k, v in el.items():
                    if k in parse_keys.keys():
                        if not isinstance(v, parse_keys[k]['type']):
                            raise ValueError(f"{k}'s value should be {parse_keys[k]['type']}")
                    else:
                        # 弹出不在验证字典中的字段
                        el.pop(k)
            else:
                raise ValueError('This SHOULD be a dict inside')
    else:
        raise ValueError('This should be a list outside')

    return value


def enough_reduce_type(value):
    parse_keys = {'with_amount': {'required': True, 'type': int},
                  'reduced_amount': {'type': int}}
    return type_base(parse_keys, value)


def enough_gifts_type(value):
    parse_keys = {'with_quantity': {'need_one': True, 'type': int},
                  'with_amount': {'need_one': True, 'type': int},
                  'free_quantity': {'required': True, 'type': int},
                  'gifts': {'required': True, 'type': list}}
    return type_base(parse_keys, value)


def enough_pay_more_type(value):
    parse_keys = {'with_amount': {'required': True, 'type': int},
                  'pay_more': {'required': True, 'type': float},
                  'pay_more_quantity': {'type': int},
                  'gifts': {'required': True, 'type': list}}
    return type_base(parse_keys, value)


def combo_type(value):
    parse_keys = {'combo_price': {'required': True, 'type': float},
                  'gifts': {'required': True, 'type': list}}
    return type_base(parse_keys, value)


def presell_type(value):
    parse_keys = {'presell_price': {'required': True, 'type': float},
                  'presell_multiple': {'required': True, 'type': float}}
    return type_base(parse_keys, value)


def seckill_type(value):
    parse_keys = {'id': {'required': True, 'type': str},
                  'seckill_price': {'required': True, 'type': float},
                  'per_user': {'type': int}}
    return type_base(parse_keys, value)


def checkout_sku_type(value):
    parse_keys = {'id': {'required': True, 'type': str},
                  'quantity': {'required': True, 'type': int}}
    return type_base(parse_keys, value)


def upload_file_type(type_id, mime_type):
    type_dict = {"0": "image", "1": "video", "2": "application"}
    return True if type_dict[str(type_id)] in mime_type else False
