from fabric.api import cd, run, local

from .containers import conf
from .task import Task


__all__ = ['init', 'push']


class Init(Task):
    def do(self):
        with cd(self.conf.src_path):
            run('git init')
            # allow update current branch
            run('git config receive.denyCurrentBranch ignore')

init = Init()


class Push(Task):
    @conf
    def branch(self):
        return self.conf.get('branch', 'master')

    def do(self):
        local('git push --force '
              'ssh://%(user)s@%(host)s/~%(user)s/src/%(instance_name)s/ '
              '%(branch)s' % self.conf)

        with cd(self.conf.src_path):
            run('git checkout --force %(branch)s' % self.conf)

push = Push()
