from fabric.api import cd, run, local

from fabdeploy.containers import conf
from fabdeploy.task import Task


__all__ = ['init', 'push']


class Init(Task):
    def do(self):
        with cd(self.conf.src_dir):
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

        with cd(self.conf.src_dir):
            run('git checkout --force %(branch)s' % self.conf)

push = Push()
