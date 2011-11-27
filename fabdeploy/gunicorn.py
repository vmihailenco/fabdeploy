from .task import Task
from .utils import upload_config_template


__all__ = ['push_config']


class PushConfig(Task):
    def do(self):
        upload_config_template('gunicorn.conf.py', context=self.conf)

push_config = PushConfig()
