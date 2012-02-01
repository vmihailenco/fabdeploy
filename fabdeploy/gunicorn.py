from fabric.api import puts, sudo

import supervisor
from .task import Task
from .utils import upload_config_template


__all__ = [
    'push_config',
    'reload_with_supervisor',
]


class PushConfig(Task):
    def do(self):
        upload_config_template('gunicorn.conf.py', context=self.conf)

push_config = PushConfig()


class ReloadWithSupervisor(Task):
    def do(self):
        pid = int(supervisor.pid_program.run(program='gunicorn'))
        if not pid:
            puts('Gunicorn is not running (pid=%s). Skipping...' % pid)
            return
        sudo('kill -HUP %s' % pid)

reload_with_supervisor = ReloadWithSupervisor()
