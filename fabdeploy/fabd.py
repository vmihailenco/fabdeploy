from fabric.api import run, sudo, puts

from fabdeploy.task import Task
from fabdeploy.utils import run_as_sudo


__all__ = ['mkdirs', 'remove_src', 'debug']


class Mkdirs(Task):
    def do(self):
        dirpathes = []
        for k, v in self.conf.items():
            if k.endswith('_dir'):
                dirpathes.append(v)

        run('mkdir --parents %s' % ' '.join(dirpathes))

mkdirs = Mkdirs()


class RemoveSrc(Task):
    @run_as_sudo
    def do(self):
        sudo('rm --recursive --force %(src_dir)s' % self.conf)

remove_src = RemoveSrc()


class Debug(Task):
    def do(self):
        puts(self.conf[self.conf.var])

debug = Debug()
