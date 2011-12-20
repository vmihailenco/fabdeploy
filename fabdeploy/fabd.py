import pprint

from fabric.api import env, run, sudo, puts, abort

from .base import setup_conf
from .task import Task


__all__ = ['mkdirs', 'remove_src', 'debug', 'conf']


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
    """Print config variable."""

    def do(self):
        if self.conf['var']:
            puts(self.conf[self.conf.var])
        else:
            puts('\n' + pprint.pformat(dict(self.conf)))

    def run(self, var=None):
        super(Debug, self).run(var=var)

debug = Debug()


class Conf(Task):
    def do(self):
        try:
            import fabconf as config
        except ImportError:
            abort('Can not import fabconf.py.')

        name = '%s_CONF' % self.conf.name.upper()
        conf = getattr(config, name)

        env.conf = setup_conf(conf)
        env.hosts = [env.conf.address]

    def run(self, name, **kwargs):
        kwargs.setdefault('name', name)
        return super(Conf, self).run(**kwargs)

conf = Conf()
