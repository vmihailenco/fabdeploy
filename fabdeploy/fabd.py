import os
import ast
import shutil
import logging

from fabric.api import env, run, sudo, puts, abort, settings, hide

from . import users, tar, ssh
from .containers import conf as conf_dec
from .task import Task


__all__ = [
    'mkdirs',
    'remove_src',
    'debug',
    'conf',
    'default_conf',
    'create_user',
    'create_configs',
    'push_bin',
]


logger = logging.getLogger('fabdeploy.fabd')


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

    def get_conf(self):
        try:
            import fabconf as config
        except ImportError:
            abort('Can not import fabconf.py.')

        name = self._conf_name(self.conf.name)
        conf = getattr(config, name)(name='fabd.conf')
        conf.set_conf_value('conf_name', self.conf.name, keep_user_value=True)

        return conf

    def create_conf(self):
        conf = self.get_conf()
        for k, v in self.task_kwargs.items():
            conf[k] = v
        return conf

    def do(self):
        env.conf = self.create_conf()
        env.hosts = [env.conf.address]

    def run(self, name, **kwargs):
        kwargs.setdefault('name', name)
        return super(Conf, self).run(**kwargs)

conf = Conf()


class DefaultConf(Conf):
    def get_conf(self):
        from .containers import DefaultConf
        return DefaultConf(name='default')

    def run(self, **kwargs):
        return super(Conf, self).run(**kwargs)

default_conf = DefaultConf()


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


class CreateConfigs(Task):
    """Creates config_templates directory with all available configs."""

    @conf_dec
    def configs_src(self):
        return os.path.join(
            os.path.dirname(__file__), 'config_templates')

    @conf_dec
    def configs_target(self):
        return os.path.join(os.getcwd(), 'config_templates')

    def do(self):
        for (dirpath, dirnames, filenames) in os.walk(self.conf.configs_src):
            for filename in filenames:
                src_filepath = os.path.join(dirpath, filename)
                name = src_filepath.replace(self.conf.configs_src + '/', '')
                target_filepath = os.path.join(
                    self.conf.configs_target, name)
                if os.path.exists(target_filepath):
                    continue
                puts('Copying %s...' % filename)
                try:
                    os.makedirs(os.path.dirname(target_filepath))
                except OSError, exc:
                    logger.debug('CreateConfigs: %s' % exc)
                shutil.copyfile(src_filepath, target_filepath)

create_configs = CreateConfigs()


class PushBin(Task):
    @conf_dec
    def bin_src(self):
        return os.path.join(os.path.dirname(__file__), 'bin')

    @conf_dec
    def bin_target(self):
        return self.conf.fabdeploy_bin_path

    def do(self):
        tar.push.run(
            src_path=self.conf.bin_src,
            target_path=self.conf.bin_target)

push_bin = PushBin()


class Bin(Task):
    @conf_dec
    def cmd(self):
        return 'python %(fabdeploy_bin_path)s/%(program)s.py %(args)s'

    def do(self):
        with settings(hide('everything')):
            output = run(self.conf.cmd)
        return ast.literal_eval(output)

bin = Bin()
