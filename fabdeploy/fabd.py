import pprint

from fabric.api import env, run, sudo, puts, abort

from . import users, ssh
from .base import setup_conf
from .containers import conf as conf_dec
from .task import Task


__all__ = [
    'mkdirs',
    'remove_src',
    'debug',
    'conf',
    'empty_conf',
    'create_user'
]


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
    def base_conf(self):
        try:
            import fabconf as config
        except ImportError:
            abort('Can not import fabconf.py.')

        name = '%s_CONF' % self.conf.name.upper()
        conf = getattr(config, name)
        conf.update(**self._kwargs)

        return conf

    def do(self):
        env.conf = setup_conf(self.base_conf())
        env.hosts = [env.conf.address]

    def run(self, name, **kwargs):
        kwargs.setdefault('name', name)
        self._kwargs = kwargs
        return super(Conf, self).run(**kwargs)

conf = Conf()


class EmptyConf(Conf):
    def base_conf(self):
        return self._kwargs

    def run(self, **kwargs):
        self._kwargs = kwargs
        return super(Conf, self).run()

empty_conf = EmptyConf()


class CreateUser(Task):
    @conf_dec
    def fabd_user(self):
        return 'fabdeploy'

    def do(self):
        users.create.run(user=self.conf.fabd_user)
        ssh.push_key.run(
            user=self.conf.fabd_user,
            pub_key_file='~/.ssh/id_rsa.pub')
        users.grant_sudo.run(user=self.conf.fabd_user)

create_user = CreateUser()
