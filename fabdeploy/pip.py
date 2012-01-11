from fabric.api import sudo, run

from .containers import conf
from .task import Task
from .utils import home_path, upload_config_template


__all__ = ['install', 'push_config']


class Install(Task):
    USE_SUDO = True

    def cmd(self, command):
        if self.USE_SUDO:
            return sudo(command)
        else:
            return run(command)

    @conf
    def options(self):
        options = self.conf.get('options', '')
        if self.conf.get('upgrade', False):
            options += ' --upgrade'
        if self.conf.get('cache', True):
            if '_pip_cache' not in self.conf:
                sudo('mkdir --parents %(pip_cache_path)s' % self.conf)
                sudo('chmod 0777 %(pip_cache_path)s' % self.conf)
                self.conf.set_globally('_pip_cache', True)
            options += ' --download-cache %(pip_cache_path)s' % self.conf
        return options

    def do(self):
        self.cmd('pip install %(options)s %(app)s' % self.conf)

install = Install()


class PushConfig(Task):
    """Sets up pip.conf file"""

    @conf
    def home_path(self):
        return home_path(self.conf.user)

    def do(self):
        sudo('mkdir --parents %(home_path)s/.pip' % self.conf)
        upload_config_template(
            'pip.conf',
            '%(home_path)s/.pip/pip.conf' % self.conf,
            use_sudo=True)
        sudo('chown --recursive %(user)s:%(user)s %(home_path)s/.pip' %
             self.conf)

push_config = PushConfig()
