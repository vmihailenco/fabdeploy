from fabric.api import sudo, settings

from fabdeploy.task import Task as BaseTask, conf
from fabdeploy.utils import upload_config_template, run_as_sudo


__all__ = ['push_config', 'disable_config', 'emperor']


class Task(BaseTask):
    @conf
    def sites_available_dir(self):
        return '/etc/uwsgi/sites-available'

    @conf
    def sites_enabled_dir(self):
        return '/etc/uwsgi/sites-enabled'

    @conf
    def config(self):
        return '%(sites_available_dir)s/%(instance_name)s.ini' % self.conf

    @conf
    def enabled_config(self):
        return '%(sites_enabled_dir)s/%(instance_name)s.ini' % self.conf


class PushConfig(Task):
    @run_as_sudo
    def do(self):
        sudo('mkdir --parents %s %s' % (self.conf.sites_available_dir,
                                       self.conf.sites_enabled_dir))
        upload_config_template('uwsgi.ini', self.conf.config,
            context=self.conf, use_sudo=True)
        with settings(warn_only=True):
            sudo('ln --symbolic %(config)s %(enabled_config)s' % self.conf)

push_config = PushConfig()


class DisableConfig(Task):
    @run_as_sudo
    def do(self):
        sudo('rm %(enabled_config)s' % self.conf)

disable_config = DisableConfig()


class Emperor(Task):
    @run_as_sudo
    def do(self):
        sudo('%(env_dir)s/bin/uwsgi --emperor %(sites_enabled_dir)s '
             '--daemonize /var/log/uwsgi-emperor.log' % self.conf)

emperor = Emperor()
