from fabric.api import sudo, task

from . import system
from .containers import conf
from .task import Task


__all__ = ['install', 'add_user', 'add_vhost', 'set_permissions']


@task
def install():
    system.aptitude_install.run(packages='rabbitmq-server')


class AddUser(Task):
    def do(self):
        sudo('rabbitmqctl add_user '
             '%(rabbitmq_user)s %(rabbitmq_password)s' % self.conf)

add_user = AddUser()


class AddVhost(Task):
    def do(self):
        sudo('rabbitmqctl add_vhost %(rabbitmq_vhost)s' % self.conf)

add_vhost = AddVhost()


class SetPermissions(Task):
    @conf
    def configure(self):
        return '.*'

    @conf
    def write(self):
        return '.*'

    @conf
    def read(self):
        return '.*'

    def do(self):
        sudo('rabbitmqctl set_permissions '
             '-p %(rabbitmq_user)s %(rabbitmq_vhost)s '
             '"%(configure)s" "%(write)s" "%(read)s"' % self.conf)

set_permissions = SetPermissions()
