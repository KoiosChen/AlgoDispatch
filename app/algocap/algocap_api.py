from flask import request, send_file
from flask_restplus import Resource, reqparse
from ..models import AlgoCap, FDFS_URL
from . import algocap
from .. import default_api, logger
from ..decorators import permission_required
from ..swagger import return_dict
import urllib.request

algocap_ns = default_api.namespace('algocap', path='/algocap',
                                   description='抓包脚本配置下载接口')

return_json = algocap_ns.model('ReturnRegister', return_dict)


@algocap_ns.route('/<string:conf_type>')
@algocap_ns.param("conf_type", "配置文件类型，install，启动脚本；program，运行程序；yaml，启动配置文件")
class AlgoCapQuery(Resource):
    @algocap_ns.marshal_with(return_json)
    @permission_required("app.algocap.algocap_api.algocap_query.get")
    def get(self, **kwargs):
        """
        获取algocap的配置文件
        """
        try:
            conf = AlgoCap.query.filter(AlgoCap.conf_type.__eq__(kwargs['conf_type']), AlgoCap.delete_at.__eq__(None)).first()
            if not conf:
                return None, 404
            else:
                conf_file = urllib.request.urlopen(f"{FDFS_URL}{conf.path}")
                return send_file(
                    filename_or_fp=conf_file,
                    mimetype="application/octet-stream",
                    as_attachment=True,
                    attachment_filename=conf.name
                )
        except Exception as e:
            logger.error(str(e))
            return None, 404
