import re
import os
import posixpath

from fabric.api import cd, sudo, puts
from fabric.contrib import files

from .containers import conf, MissingVarException
from .task import Task
from .users import list_users
from .files import read_file, exists
from .utils import home_path, split_lines


__all__ = [
    'push_key',
    'list_authorized_files',
    'list_keys',
    'enable_key',
    'disable_key',
]


class PushKey(Task):
    @conf
    def abs_pub_key_file(self):
        return os.path.expanduser(self.conf.pub_key_file)

    def do(self):
        with open(self.conf.abs_pub_key_file, 'rt') as f:
            ssh_key = f.read()

        with cd(home_path(self.conf.user)):
            sudo('mkdir --parents .ssh')
            files.append('.ssh/authorized_keys', ssh_key, use_sudo=True)
            sudo('chown --recursive %(user)s:%(user)s .ssh' % self.conf)

push_key = PushKey()


class SshManagementTask(Task):
    def before_do(self):
        super(SshManagementTask, self).before_do()
        self.conf.setdefault('exclude_users', [])

    @conf
    def authorized_file(self):
        if 'user' in self.conf and self.conf.user:
            return posixpath.join(
                home_path(self.conf.user), '.ssh', 'authorized_keys')
        raise MissingVarException()


class ListAuthorizedFiles(SshManagementTask):
    def get_authorized_files(self, exclude_users=None):
        users = list_users.get_users(exclude_users=exclude_users)

        authorized_files = []
        for user in users:
            dirpath = home_path(user)
            authorized_file = '%s/.ssh/authorized_keys' % dirpath
            if exists(authorized_file, use_sudo=True, shell=False):
                authorized_files.append((user, authorized_file))
        return authorized_files

    def do(self):
        authorized_files = self.get_authorized_files(
            exclude_users=self.conf.exclude_users)
        for user, authorized_file in authorized_files:
            puts(authorized_file)

list_authorized_files = ListAuthorizedFiles()


class ListKeys(SshManagementTask):
    def get_keys(self, authorized_file):
        body = read_file(authorized_file, use_sudo=True, shell=False)
        return filter(lambda row: not row.startswith('#'), split_lines(body))

    def do(self):
        authorized_files = list_authorized_files.get_authorized_files()
        for user, auth_file in authorized_files:
            puts(user)
            puts('-' * 40)
            for key in self.get_keys(auth_file):
                puts(key)
            puts('-' * 40)

list_keys = ListKeys()


class DisableKey(SshManagementTask):
    def disable_key(self, authorized_file, key):
        key_regex = re.escape(key)
        key_regex = key_regex.replace('\/', '/')
        key_regex = '^%s$' % key_regex
        backup = '.%s.bak' % self.conf.current_time
        files.comment(authorized_file, key_regex, use_sudo=True, backup=backup)

    def do(self):
        if 'authorized_file' in self.conf:
            self.disable_key(self.conf.authorized_file, self.conf.key)
        else:
            authorized_files = list_authorized_files.get_authorized_files(
                exclude_users=self.conf.exclude_users)
            for user, authorized_file in authorized_files:
                self.disable_key(authorized_file, self.conf.key)

disable_key = DisableKey()


class EnableKey(SshManagementTask):
    def enable_key(self, authorized_file, key):
        backup = '.%s.bak' % self.conf.current_time
        regex = '%s' % re.escape(key)
        commented_key = '#' + regex

        if files.contains(
                authorized_file, commented_key, exact=True, use_sudo=True):
            files.uncomment(authorized_file, regex, use_sudo=True,
                            backup=backup)
        else:
            files.append(authorized_file, key, use_sudo=True)

    def do(self):
        if 'authorized_file' in self.conf:
            self.enable_key(self.conf.authorized_file, self.conf.key)
        else:
            authorized_files = list_authorized_files.get_authorized_files(
                exclude_users=self.conf.exclude_users)
            for user, authorized_file in authorized_files:
                self.enable_key(authorized_file, self.conf.key)

enable_key = EnableKey()
