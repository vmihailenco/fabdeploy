from fabric.api import run, puts, sudo

from fabdeploy.task import Task


__all__ = ['mkdirs', 'remove_src', 'debug']


class Mkdirs(Task):
    def do(self):
        dirpathes = []
        for k, v in self.conf.items():
            if k.endswith('_path'):
                dirpathes.append(v)

        run('mkdir --parents %s' % ' '.join(dirpathes))

mkdirs = Mkdirs()


class RemoveSrc(Task):
    def do(self):
        sudo('rm --recursive --force %(src_path)s' % self.conf)

remove_src = RemoveSrc()


class Debug(Task):
    def do(self):
        puts(self.conf[self.conf.var])

    def run(self, var):
        super(Debug, self).run(var=var)

debug = Debug()
