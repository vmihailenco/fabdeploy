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


class GitTask(Task):
    @conf
    def repo_branch(self):
        return self.conf.get('repo_branch', 'master')


class Init(GitTask):
    def do(self):
        with cd(self.conf.release_path):
            run('git init')
            # allow update current branch
            run('git config receive.denyCurrentBranch ignore')

init = Init()


class Push(GitTask):
    @conf
    def dir(self):
        return self.conf.release_path \
            .replace(self.conf.home_path, '') \
            .strip(os.sep)

    @conf
    def options(self):
        return ''

    def do(self):
        local('git push '
              'ssh://%(user)s@%(host)s/~%(user)s/%(dir)s '
              '%(repo_branch)s' % self.conf)

        with cd(self.conf.release_path):
            run('git checkout --force %(repo_branch)s' % self.conf)

push = Push()


class Pull(GitTask):
    def do(self):
        with cd(self.conf.release_path):
            run('git pull %(repo_origin)s %(repo_branch)s' % self.conf)
            run('git checkout %(repo_branch)s' % self.conf)

pull = Pull()


class Tag(GitTask):
    def do(self):
        run('git tag %(release)s' % self.conf)

tag = Tag()


class LastCommit(GitTask):
    def do(self):
        with cd(self.conf.release_path):
            return run('git log -n 1 --pretty=oneline')

last_commit = LastCommit()
