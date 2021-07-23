import urllib.request
from kubernetes import client, config
from kubernetes.watch import Watch
from app.models import KubeMaster, Jobs, FDFS_URL
from app import logger
from app.common import false_return, success_return
import yaml
import time


class KubeMgmt:
    def __init__(self, master, namespace='default'):
        # Configs can be set in Configuration class directly or using helper utility
        config.load_kube_config(config_file=KubeMaster.get(master))
        self.v1 = client.CoreV1Api()
        self.batch = client.BatchV1Api()
        self.namespace = namespace
        self.watcher = Watch()
        self.cfg = None
        self.job_names = list()

    def list_all_pods(self):
        print("Listing pods with their IPs:")
        ret = self.v1.list_pod_for_all_namespaces(watch=False)
        for i in ret.items:
            print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

    def load_yaml(self, job_id):
        try:
            job = Jobs.query.get(job_id)
            if not job:
                raise Exception(f"job {job_id} does not exist")
            file_path = job.config_files.query.filter_by(status=1).first().storage
            self.cfg = yaml.safe_load(urllib.request.urlopen(f"{FDFS_URL}{file_path}"))
            print(self.cfg)
        except Exception as e:
            return false_return(message=str(e))

    def start_job(self, job_id=None):
        try:
            if job_id is not None:
                self.load_yaml(job_id)

            job = self.batch.create_namespaced_job(namespace=self.namespace, body=self.cfg)
            assert isinstance(job, client.V1Job)
            return success_return(message='k8s job create success', data={'job_name': self.cfg['metadata']['name']})
        except Exception as e:
            logger.error(str(e))
            return false_return(message=str(e))

    def watch_job(self, job_name, namespace=None):
        if namespace is None:
            namespace = self.namespace
        for event in self.watcher.stream(self.batch.list_namespaced_job, namespace=namespace,
                                         label_selector=f'job-name={job_name}'):
            assert isinstance(event, dict)
            job = event['object']
            assert isinstance(job, client.V1Job)
            if job.status:
                failed = 0 if job.status.failed is None else job.status.failed
                succeeded = 0 if job.status.succeeded is None else job.status.succeeded
                if job.spec.completions == (failed + succeeded):
                    print(f'Job completed at {job.status.completion_time}, {failed=}, {succeeded=}')
                    break
