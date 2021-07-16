from flask_restplus import fields, reqparse

head_parser = reqparse.RequestParser()
head_parser.add_argument('Authorization', required=True, location='headers')

return_dict = {'code': fields.String(required=True, description='success | false'),
               'data': fields.Raw(description='string or json'),
               'message': fields.String(description='成功或者失败的文字信息')}

page_parser = reqparse.RequestParser()
page_parser.add_argument('page', help='true | false, 是否分页', location='args')
page_parser.add_argument('current', type=int, help='当前页, 第一页为1， 必须传大于0的整数', location='args')
page_parser.add_argument('size', type=int, help='当前页行数, 大于0的整数', location='args')
