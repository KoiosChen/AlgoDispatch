from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from qcloud_cos import CosClientError
from qcloud_cos import CosServiceError
from app.common import success_return, false_return, submit_return
from app import logger, db


def delete_object(obj):
    cos_client = QcloudCOS()
    try:
        cos_client.delete(obj.obj_key)
    except Exception as e:
        return false_return(message=f"删除cos中图片失败"), 400
    db.session.delete(obj)
    return submit_return("已删除图片", "删除图片失败")


class QcloudCOS:
    def __init__(self, **kwargs):
        # -*- coding=utf-8
        # appid 已在配置中移除,请在参数 Bucket 中带上 appid。Bucket 由 BucketName-APPID 组成
        # 1. 设置用户配置, 包括 secretId，secretKey 以及 Region
        secret_id = kwargs.get("secret_id")
        secret_key = kwargs.get("secret_key")
        region = kwargs.get("region")
        bucket_id = kwargs.get("bucket_id")
        self.__secret_id = 'AKIDMTZaicplwwgEYiRIi7jw9Bqj7JGxuuBH' if not secret_id else secret_id
        self.__secret_key = 'DDybLuLEtIJmP6bqtg0WmVszLBsLktlP' if not secret_key else secret_key
        self.__region = 'ap-shanghai' if not region else region
        self.__bucket_id = 'shengzhuan-1302873950' if not bucket_id else bucket_id
        self.url = f"{self.__bucket_id}.cos.{self.__region}.myqcloud.com"
        token = None  # 使用临时密钥需要传入 Token，默认为空，可不填
        self.scheme = 'https'  # 指定使用 http/https 协议来访问 COS，默认为 https，可不填
        config = CosConfig(Region=self.__region, SecretId=self.__secret_id, SecretKey=self.__secret_key, Token=token,
                           Scheme=self.scheme)
        # 2. 获取客户端对象
        self.client = CosS3Client(config)

    def upload(self, object_key, body, storage_class="STANDARD"):
        try:
            response = self.client.put_object(
                Bucket=self.__bucket_id,
                Body=body,
                Key=object_key,
                StorageClass=storage_class
            )
            logger.debug(f">>> cos upload response {response}")
            result = {'bucket': self.__bucket_id, 'region': self.__region, 'obj_key': object_key,
                      'url': self.scheme + "://" + self.url + '/' + object_key}
            return success_return(data=result, message=f"{response}")
        except Exception as e:
            return false_return(e)

    def delete(self, object_key):
        response = self.client.delete_object(
            Bucket=self.__bucket_id,
            Key=object_key
        )
        return success_return(message=f">>> cos delete response {response}")
