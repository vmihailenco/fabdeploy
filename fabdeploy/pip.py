from fabric.api import sudo

from fabdeploy.containers import conf
from fabdeploy.task import Task
from fabdeploy.utils import get_home_path, upload_config_template


__all__ = ['install', 'setup_conf']


class Install(Task):
    def before_do(self):
        self.conf.setdefault('upgrade', False)

    @conf
    def options(self):
        options = self.conf.get('options', '')
        if self.conf.upgrade:
            options += ' --upgrade'
        return options

    def do(self):
        sudo('pip install %(options)s %(app)s' % self.conf)

install = Install()


class SetupConf(Task):
    """Sets up pip.conf file"""

    @conf
    def home_path(self):
        return get_home_path(self.conf.user)

    def do(self):
        sudo('mkdir --parents %(home_path)s/.pip' % self.conf)
        upload_config_template(
            'pip.conf',
            '%(home_path)s/.pip/pip.conf' % self.conf,
            use_sudo=True)
        sudo('chown --recursive %(user)s:%(user)s %(home_path)s/.pip' %
             self.conf)

setup_conf = SetupConf()
