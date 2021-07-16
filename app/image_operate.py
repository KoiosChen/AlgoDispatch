from app.models import ObjStorage
from app.common import success_return, false_return, submit_return


def operate(obj, imgs, action):
    if obj and imgs:
        for img in imgs:
            image = ObjStorage.query.get(img)
            if image:
                if image not in obj.objects:
                    getattr(obj.objects, action)(image)
            else:
                return false_return(message="图片不存在"), 400
        return submit_return(f"<{obj.id}>增加图片成功", f"<{obj.id}>增加图片失败")
    elif obj and not imgs:
        obj.objects = []
        return submit_return(f"<{obj.id}>清空图片成功", f"<{obj.id}>清空图片失败")
    else:
        return false_return(message=f"<{obj.id}>不存在"), 400
