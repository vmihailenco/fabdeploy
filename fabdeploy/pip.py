from fabdeploy.containers import conf
from fabdeploy.task import Task
from fabdeploy.utils import run_as_sudo, sudo


__all__ = ['pip_install']


class PipInstall(Task):
    def before_do(self):
        self.conf.setdefault('upgrade', False)

    @conf
    def options(self):
        options = self.conf.get('options', '')
        if self.conf.upgrade:
            options += ' --upgrade'
        return options

    @run_as_sudo
    def do(self):
        sudo('pip install %(options)s '
            '--download-cache %(pip_cache_dir)s '
            '%(app)s' % self.conf)

pip_install = PipInstall()
