from fabdeploy.task import Task
from fabdeploy.utils import upload_config_template


__all__ = ['push_config']


class PushConfig(Task):
    def do(self):
        upload_config_template('gunicorn.conf.py', context=self.conf,
                               use_jinja=True)

push_config = PushConfig()
