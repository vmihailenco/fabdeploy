from fabric.api import sudo, settings

from .task import Task
from .containers import conf
from .utils import upload_config_template
from . import system
from . import pip


__all__ = [
    'install_deps',
    'install',
    'push_config',
    'disable_config',
    'emperor',
]


class InstallDeps(Task):
    def do(self):
        system.package_install(
            packages='build-essential python-dev libxml2-dev')

install_deps = InstallDeps()


class Install(Task):
    def do(self):
        return pip.install('uwsgi')

install = Install()


class ConfigTask(Task):
    @conf
    def sites_available_path(self):
        return '/etc/uwsgi/sites-available'

    @conf
    def sites_enabled_path(self):
        return '/etc/uwsgi/sites-enabled'

    @conf
    def config(self):
        return '%(sites_available_path)s/%(instance_name)s.ini' % self.conf

    @conf
    def enabled_config(self):
        return '%(sites_enabled_path)s/%(instance_name)s.ini' % self.conf


class PushConfig(ConfigTask):
    def do(self):
        sudo(
            'mkdir --parents %(sites_available_path)s %(sites_enabled_path)s' %
             self.conf)
        upload_config_template(
            'uwsgi.ini', self.conf.config, context=self.conf, use_sudo=True)
        with settings(warn_only=True):
            sudo('ln --symbolic %(config)s %(enabled_config)s' % self.conf)

push_config = PushConfig()


class DisableConfig(ConfigTask):
    def do(self):
        sudo('rm %(enabled_config)s' % self.conf)

disable_config = DisableConfig()


class Emperor(Task):
    def do(self):
        sudo(
            '%(env_path)s/bin/uwsgi --emperor %(sites_enabled_path)s '
            '--daemonize /var/log/uwsgi-emperor.log' % self.conf)

emperor = Emperor()
