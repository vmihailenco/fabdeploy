from fabric.api import sudo, settings

from . import system
from .containers import conf
from .task import Task
from .utils import upload_config_template


__all__ = [
    'install',
    'restart',
    'reload',
]


class Install(Task):
    def do(self):
        if self.conf.os in ['lucid', 'maverick', 'natty']:
            sudo('add-apt-repository ppa:nginx/stable')
            system.aptitude_update.run(force=True)
            system.aptitude_install.run(packages='nginx')
        else:
            options = {'lenny': '-t lenny-backports'}
            system.aptitude_install.run(
                packages='nginx',
                options=options.get(self.conf.os, ''))
        sudo('rm --force /etc/nginx/sites-enabled/default')

install = Install()


class PushConfigTask(Task):
    @conf
    def config(self):
        return '/etc/nginx/sites-available/%(instance_name)s'

    @conf
    def enabled_config(self):
        return '/etc/nginx/sites-enabled/%(instance_name)s'

    def do(self):
        upload_config_template(
            self.conf.config_template,
            self.conf.config,
            context=self.conf,
            use_sudo=True)
        with settings(warn_only=True):
            sudo('ln --symbolic %(config)s %(enabled_config)s' % self.conf)


class PushUwsgiConfig(PushConfigTask):
    @conf
    def config_template(Task):
        return 'nginx_uwsgi.config'

push_uwsgi_config = PushUwsgiConfig()


class Restart(Task):
    def do(self):
        sudo('invoke-rc.d nginx restart')

restart = Restart()


class Reload(Task):
    def do(self):
        sudo('invoke-rc.d nginx reload')

reload = Reload()
