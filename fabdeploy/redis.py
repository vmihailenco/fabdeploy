from fabric.api import sudo

from . import system
from .task import Task


__all__ = ['add_ppa', 'install']


class AddPpa(Task):
    def do(self):
        if self.conf.os in ['lucid', 'maverick', 'natty']:
            sudo('add-apt-repository ppa:rwky/redis')
            system.aptitude_update.run(force=True)

add_ppa = AddPpa()


class Install(Task):
    def do(self):
        system.aptitude_install.run(packages='redis-server')

install = Install()
