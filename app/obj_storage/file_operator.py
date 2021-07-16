from flask_restplus import Resource, reqparse
from ..models import ObjStorage, Permission
from .. import logger
from ..common import success_return, false_return, session_commit
from ..public_method import new_data_obj, get_table_data
from ..decorators import permission_required
from ..swagger import head_parser, return_dict, page_parser
from werkzeug.datastructures import FileStorage
from .. import default_api
from app.wechat.qqcos import QcloudCOS
import uuid
from ..type_validation import upload_file_type
from PIL import Image
from io import BytesIO as Bytes2Data
import io

cos_ns = default_api.namespace('object_storage', path='/object_storage',
                               description='图片文件')

return_json = cos_ns.model('ReturnRegister', return_dict)

upload_parser = reqparse.RequestParser()
upload_parser.add_argument('prefix', type=str, help='用于区分类型，譬如banners， logo')
upload_parser.add_argument('obj_type', type=int, choices=[0, 1, 2], required=True, help='0 图片 1 视频 2 文本')
upload_parser.add_argument('file', required=True, type=FileStorage, location='files')
upload_parser.add_argument('thumbnail', type=int, choices=[0, 1], default=0, help='不传默认为0， 0：不生成缩略图，1：生成缩略图')
upload_parser.add_argument('width', type=int, help='缩略图宽度（像素）。如果thumbnail传1， 则此项必传')
upload_parser.add_argument('height', type=int, help='缩略图高度（像素）。如果thumbnail传1， 则此项必传')


class OperateObject:
    def __init__(self, **args):
        self.cos_client = QcloudCOS()
        self.upload_object = args['file']
        self.ext_name = args['filename'].split('.')[-1]
        self.object_key = args['prefix'] + '/' if args['prefix'] else ""
        self.object_key += str(uuid.uuid4()) + '.' + self.ext_name
        self.store_result = self.cos_client.upload(self.object_key,
                                                   self.upload_object.stream if hasattr(self.upload_object,
                                                                                        'stream') else self.upload_object)
        if self.store_result['code'] != 'false':
            self.store_result['data']['obj_type'] = args['obj_type']
        logger.debug(self.store_result)

    def do_upload(self):
        if self.store_result.get("code") == "success":
            new_object = new_data_obj("ObjStorage", **self.store_result.get("data"))
            if session_commit().get('code') == 'success':
                return success_return(
                    data={'object_id': new_object['obj'].id, 'path': self.store_result['data']['url']})
            else:
                self.cos_client.delete(self.store_result['obj_key'])
                return false_return(message=f"上传对象失败")
        else:
            return false_return(message="cos上传失败"), 400

    def do_delete(self):
        self.cos_client.delete(self.object_key)


@cos_ns.route('')
@cos_ns.expect(head_parser)
class ObjectStorageApi(Resource):
    @cos_ns.marshal_with(return_json)
    @cos_ns.doc(body=page_parser)
    @permission_required(Permission.USER)
    def get(self, **kwargs):
        """
        获取所有图片
        """
        args = page_parser.parse_args()
        return success_return(get_table_data(ObjStorage, args))

    @cos_ns.doc(body=upload_parser)
    @cos_ns.marshal_with(return_json)
    @permission_required(["app.img_urls.img_url.upload_img", Permission.USER])
    def post(self, **kwargs):
        """上传对象"""
        args = upload_parser.parse_args()
        logger.debug(f"upload object to storage {args}")
        upload_object = args['file']
        logger.debug(upload_object)
        args['filename'] = upload_object.filename

        if upload_file_type(args['obj_type'], upload_object.mimetype):
            if args['thumbnail'] == 1 and args['obj_type'] != 0:
                return false_return(message='非图片不可生成缩略图')

            original_obj = OperateObject(**args)
            if original_obj.store_result.get('code') == 'false':
                return false_return(message=str(original_obj.store_result)), 400
            upload_result = original_obj.do_upload()
            if upload_result.get("code") == 'false':
                return false_return(data=upload_result), 400

            if args['thumbnail'] == 0:
                return upload_result

            if not args['width'] or not args['height']:
                return false_return(message=f"生成缩略图，缺少缩略图尺寸")

            size = (args['width'], args['height'])
            im = Image.open(upload_object.stream)
            im.thumbnail(size)
            in_mem_file = io.BytesIO()
            im.save(in_mem_file, format=im.format)
            thumbnail_prefix = args['prefix'] + '/' if args['prefix'] else ""
            thumbnail_prefix += 'thumbnails'
            upload_object_name = upload_object.filename.split('.')
            im.filename = '.'.join(upload_object_name[0:-1]) + '_thumbnail.' + upload_object_name[-1]
            thumbnail_args = {'file': in_mem_file.getvalue(), 'filename': im.filename, 'prefix': thumbnail_prefix,
                              'obj_type': 0}
            thumbnail_obj = OperateObject(**thumbnail_args)
            thumbnail_upload_result = thumbnail_obj.do_upload()
            if thumbnail_upload_result.get('code') == 'success':
                upload_result['data']['thumbnail'] = thumbnail_upload_result['data']
                original_data = ObjStorage.query.get(upload_result['data']['object_id'])
                original_data.thumbnails.append(ObjStorage.query.get(thumbnail_upload_result['data']['object_id']))
                if session_commit().get('code') == 'success':
                    return upload_result
                else:
                    return false_return(message="缩略图添加数据库失败"), 400
            else:
                original_obj.do_delete()
                return false_return(message="缩略图上传失败，撤销所有上传")
        else:
            return false_return(message="上传文件格式与选择类型不匹配"), 400
