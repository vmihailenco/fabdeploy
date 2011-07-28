import os

from fabric.api import settings, sudo, puts

from fabdeploy.containers import conf
from fabdeploy.task import Task
from fabdeploy.files import list_files
from fabdeploy.utils import get_home_dir, run_as_sudo


__all__ = ['create', 'delete', 'list_users']


class Create(Task):
    @conf
    def home_dir(self):
        return get_home_dir(self.conf.user)

    @run_as_sudo
    def do(self):
        with settings(warn_only=True):
            sudo('adduser %(user)s --disabled-password --gecos ""' % self.conf)

create = Create()


class Delete(Task):
    @run_as_sudo
    def do(self):
        sudo('userdel --remove %(user)s' % self.conf)

delete = Delete()


class ListUsers(Task):
    def before_do(self):
        self.conf.setdefault('exclude_users', [])

    def get_users(self, exclude_users=None):
        if exclude_users is None:
            exclude_users = []

        users = []
        if 'root' not in exclude_users:
            users.append('root')
        for dirpath in list_files('/home'):
            user = os.path.basename(dirpath)
            if user not in exclude_users:
                users.append(user)
        return users

    def do(self):
        users = self.get_users(exclude_users=self.conf.exclude_users)
        puts(', '.join(users))

list_users = ListUsers()
