import yaml
from app import logger
from app.models import Jobs, FDFS_URL
from app.common import false_return
import urllib.request


def load_yaml(job_id):
    try:
        job = Jobs.query.get(job_id)
        if not job:
            raise Exception(f"job {job_id} does not exist")
        file_path = job.config_files.query.filter_by(status=1).first().storage
        cfg = yaml.safe_load(urllib.request.urlopen(f"{FDFS_URL}{file_path}"))
        logger.debug(f"yaml config: {cfg}")
    except Exception as e:
        return false_return(message=str(e))
