from fabric.api import puts, sudo

import supervisor
from .containers import conf
from .task import Task
from .utils import upload_config_template
from .nginx import PushConfigTask as PushNginxConfigTask


__all__ = [
    'push_config',
    'push_nginx_config',
    'reload_with_supervisor',
]


class GunicornMixin(object):
    @conf
    def gunicorn_bind(self):
        return 'unix:/tmp/gunicorn-%(server_name)s.socket'


class PushConfig(GunicornMixin, Task):
    def do(self):
        upload_config_template('gunicorn.conf.py', context=self.conf)

push_config = PushConfig()


class PushNginxConfig(GunicornMixin, PushNginxConfigTask):
    @conf
    def config_template(self):
        return 'nginx_gunicorn.config'

push_nginx_config = PushNginxConfig()


class ReloadWithSupervisor(GunicornMixin, Task):
    def do(self):
        pid = int(supervisor.pid_program.run(program='gunicorn'))
        if not pid:
            puts('Gunicorn is not running (pid=%s). Skipping...' % pid)
            return
        sudo('kill -HUP %s' % pid)

reload_with_supervisor = ReloadWithSupervisor()
