from fabric.api import sudo

from . import system
from .task import Task


__all__ = ['add_ppa', 'install', 'stop', 'remove_init_d']


class AddPpa(Task):
    def do(self):
        sudo('add-apt-repository ppa:rwky/redis')
        system.package_update.run(force=True)

add_ppa = AddPpa()


class Install(Task):
    def do(self):
        system.package_install.run(packages='redis-server')

install = Install()


class Stop(Task):
    def do(self):
        sudo('stop redis-server')

stop = Stop()


class RemoveInit(Task):
    def do(self):

        sudo('rm /etc/init/redis-server')

remove_init = RemoveInit()
