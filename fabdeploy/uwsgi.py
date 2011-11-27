from fabric.api import sudo, settings

from .task import Task as BaseTask
from .containers import conf
from .utils import upload_config_template


__all__ = ['push_config', 'disable_config', 'emperor']


class Task(BaseTask):
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


class PushConfig(Task):
    def do(self):
        sudo('mkdir --parents %s %s' % (self.conf.sites_available_path,
                                       self.conf.sites_enabled_path))
        upload_config_template('uwsgi.ini', self.conf.config,
            context=self.conf, use_sudo=True)
        with settings(warn_only=True):
            sudo('ln --symbolic %(config)s %(enabled_config)s' % self.conf)

push_config = PushConfig()


class DisableConfig(Task):
    def do(self):
        sudo('rm %(enabled_config)s' % self.conf)

disable_config = DisableConfig()


class Emperor(Task):
    def do(self):
        sudo('%(env_path)s/bin/uwsgi --emperor %(sites_enabled_path)s '
             '--daemonize /var/log/uwsgi-emperor.log' % self.conf)

emperor = Emperor()
