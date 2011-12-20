import os

from fabric.api import settings, sudo, puts
from fabric.contrib import files

from .task import Task
from .files import list_files


__all__ = ['create', 'delete', 'grant_sudo', 'list_users']


class Create(Task):
    def do(self):
        with settings(warn_only=True):
            sudo('adduser %(user)s --disabled-password --gecos ""' % self.conf)

create = Create()


class Delete(Task):
    def do(self):
        sudo('userdel --remove %(user)s' % self.conf)

delete = Delete()


class GrantSudo(Task):
    def grant(self):
        return '%(user)s ALL=(ALL) NOPASSWD: ALL' % self.conf

    def do(self):
        files.append('/etc/sudoers', self.grant(), use_sudo=True)

grant_sudo = GrantSudo()


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
            if user not in exclude_users and \
               files.contains('/etc/passwd', user):
                users.append(user)
        return users

    def do(self):
        users = self.get_users(exclude_users=self.conf.exclude_users)
        puts(', '.join(users))

list_users = ListUsers()
