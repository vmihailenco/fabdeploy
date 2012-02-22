import os

from fabric.api import cd, run, local

from .containers import conf
from .task import Task


__all__ = [
    'init',
    'push',
    'pull',
    'tag',
    'last_commit',
]


class Init(Task):
    def do(self):
        with cd(self.conf.src_path):
            run('git init')
            # allow update current branch
            run('git config receive.denyCurrentBranch ignore')

init = Init()


class Push(Task):
    @conf
    def dir(self):
        return self.conf.src_path \
            .replace(self.conf.home_path, '') \
            .strip(os.sep)

    @conf
    def options(self):
        return ''

    @conf
    def branch(self):
        return self.conf.get('branch', 'master')

    def do(self):
        local('git push '
              'ssh://%(user)s@%(host)s/~%(user)s/%(dir)s '
              '%(branch)s' % self.conf)

        with cd(self.conf.src_path):
            run('git checkout --force %(branch)s' % self.conf)

push = Push()


class Pull(Task):
    def do(self):
        with cd(self.conf.src_path):
            run('git pull %(git_origin)s %(branch)s' % self.conf)
            run('git checkout %(branch)s' % self.conf)

pull = Pull()


class Tag(Task):
    def do(self):
        run('git tag %(version)s' % self.conf)

tag = Tag()


class LastCommit(Task):
    def do(self):
        with cd(self.conf.src_path):
            return run('git log -n 1 --pretty=oneline')

last_commit = LastCommit()
