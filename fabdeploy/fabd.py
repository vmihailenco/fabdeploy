import pprint

from fabric.api import env, run, sudo, puts, abort

from . import users, ssh
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
        home_dirs, sudo_dirs = [], []
        for k, v in self.conf.items():
            if k.endswith('_path'):
                if v.startswith(self.conf.home_path):
                    home_dirs.append(v)
                else:
                    sudo_dirs.append(v)

        run('mkdir --parents %s' % ' '.join(home_dirs))
        sudo('mkdir --parents %s' % ' '.join(sudo_dirs))

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
        if 'var' in self.conf:
            puts(self.conf[self.conf.var])
        else:
            out = '\n'
            for k, v in self.conf.items():
                out += '%s = %s\n' % (k, v)
            puts(out)

    def run(self, var=None, **kwargs):
        if var is not None:
            kwargs.setdefault('var', var)
        super(Debug, self).run(**kwargs)

debug = Debug()


class Conf(Task):
    def _conf_name(self, name):
        return ''.join([p[:1].upper() + p[1:] for p in name.split('_')]) + 'Conf'

    def create_conf(self):
        try:
            import fabconf as config
        except ImportError:
            abort('Can not import fabconf.py.')

        name = self._conf_name(self.conf.name)
        conf = getattr(config, name)(name='fabd.conf')
        conf.set_globally('conf_name', self.conf.name)

        return conf

    def do(self):
        env.conf = self.create_conf()
        env.hosts = [env.conf.address]

    def run(self, name, **kwargs):
        kwargs.setdefault('name', name)
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
