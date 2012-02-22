from fabric.api import sudo, abort

from . import system
from .task import Task


__all__ = ['install']


class Install(Task):
    def do(self):
        if self.conf.os in ['lucid', 'maverick', 'natty']:
            sudo('add-apt-repository ppa:rwky/redis')
            system.aptitude_update.run(force=True)
            system.aptitude_install.run(packages='redis-server')
        else:
            abort('Fabdeploy can not install on %(os)s yet...')
        sudo('rm --force /etc/nginx/sites-enabled/default')

install = Install()
