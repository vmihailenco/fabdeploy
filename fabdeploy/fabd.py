from fabric.api import run, puts, sudo

from fabdeploy.task import Task


__all__ = ['mkdirs', 'remove_src', 'debug']


class Mkdirs(Task):
    """
    Create all known remote dirs.

    We treat config variables ending with ``_path`` postfix as dir.
    """

    def do(self):
        dirpathes = []
        for k, v in self.conf.items():
            if k.endswith('_path'):
                dirpathes.append(v)

        run('mkdir --parents %s' % ' '.join(dirpathes))

mkdirs = Mkdirs()


class RemoveSrc(Task):
    """
    Remove ``src_path`` dir.

    This is usefull when you want to perform clean deploy.
    See also ``virtualenv.remove``.
    """

    def do(self):
        sudo('rm --recursive --force %(src_path)s' % self.conf)

remove_src = RemoveSrc()


class Debug(Task):
    """Echo config variable."""

    def do(self):
        puts(self.conf[self.conf.var])

    def run(self, var):
        super(Debug, self).run(var=var)

debug = Debug()
