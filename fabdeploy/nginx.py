from fabric.api import sudo, settings

from fabdeploy.containers import conf
from fabdeploy.task import Task
from fabdeploy.utils import run_as_sudo, upload_config_template
from fabdeploy import system, apache


__all__ = ['install', 'restart', 'push_config_for_apache',
           'push_config_for_gunicorn']


class Install(Task):
    @run_as_sudo
    def do(self):
        options = {'lenny': '-t lenny-backports'}
        system.aptitude_install.run(packages='nginx',
                                    options=options.get(self.os, ''))
        sudo('rm --force /etc/nginx/sites-enabled/default')

install = Install()


class PushConfigForApache(Task):
    @conf
    def nginx_port(self):
        return apache.PushConfig(conf=self.conf).conf.port

    @conf
    def config(self):
        return '/etc/nginx/sites-available/%(instance_name)s' % self.conf

    @conf
    def enabled_config(self):
        return '/etc/nginx/sites-enabled/%(instance_name)s' % self.conf

    @run_as_sudo
    def do(self):
        upload_config_template('nginx.config', self.conf.config,
            context=self.conf.enabled_config, use_sudo=True)
        with settings(warn_only=True):
            sudo('ln -s %(config)s %(enabled_config)s' % self.conf)

push_config_for_apache = PushConfigForApache()


class PushConfigForGunicorn(Task):
    @conf
    def config(self):
        return '/etc/nginx/sites-available/%(instance_name)s' % self.conf

    @conf
    def enabled_config(self):
        return '/etc/nginx/sites-enabled/%(instance_name)s' % self.conf

    @run_as_sudo
    def do(self):
        upload_config_template('nginx.config', self.conf.config,
            context=self.conf, use_sudo=True)
        with settings(warn_only=True):
            sudo('ln -s %(config)s %(enabled_config)s' % self.conf)

push_config_for_gunicorn = PushConfigForGunicorn()


class Restart(Task):
    @run_as_sudo
    def do(self):
        sudo('invoke-rc.d nginx restart')

restart = Restart()
