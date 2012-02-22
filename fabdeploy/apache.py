import posixpath

from fabric.api import run, sudo
from fabric.contrib import files

from . import system
from .containers import conf
from .task import Task
from .utils import upload_config_template
from .nginx import PushConfigTask as PushNginxConfigTask


__all__ = [
    'install',
    'restart',
    'graceful',
    'wsgi_push',
    'wsgi_touch',
    'push_config',
    'push_nginx_config',
]


class Restart(Task):
    def do(self):
        sudo('invoke-rc.d apache2 stop')
        sudo('invoke-rc.d apache2 start')

restart = Restart()


class Graceful(Task):
    def do(self):
        sudo('/usr/sbin/apache2ctl graceful')

graceful = Graceful()


class Install(Task):
    def do(self):
        system.aptitude_install.run(
            packages='apache2 libapache2-mod-wsgi libapache2-mod-rpaf')
        for site in ['default', '000-default']:
            sudo('rm --force /etc/apache2/sites-enabled/' + site)
        setup_locale.run()

install = Install()


class SetupLocale(Task):
    def do(self):
        files.append('/etc/apache2/envvars',
                     ['export LANG="en_US.UTF-8"',
                      'export LC_ALL="en_US.UTF-8"'],
                     use_sudo=True)

setup_locale = SetupLocale()


class WSGITask(Task):
    @conf
    def wsgi_path(self):
        return posixpath.join(self.conf.etc_path, 'wsgi')

    @conf
    def wsgi_file(self):
        return '%(instance_name)s.py'

    @conf
    def wsgi_filepath(self):
        return posixpath.join(self.conf.wsgi_path, self.conf.wsgi_file)


class WSGIPush(WSGITask):
    def do(self):
        run('mkdir --parents %(wsgi_path)s' % self.conf)
        upload_config_template('django_wsgi.py', self.conf.wsgi_filepath)

wsgi_push = WSGIPush()


class WSGITouch(WSGITask):
    def do(self):
        run('touch %(wsgi_filepath)s' % self.conf)

wsgi_touch = WSGITouch()


class PushConfig(WSGITask):
    @conf
    def ports_filepath(self):
        return '/etc/apache2/ports.conf'

    @conf
    def ports_string(self):
        return 'Listen 127.0.0.1:%(apache_port)s'

    @conf
    def config_filepath(self):
        return '/etc/apache2/sites-available/%(instance_name)s'

    def do(self):
        files.append(
            self.conf.ports_filepath,
            self.conf.ports_string,
            use_sudo=True)

        upload_config_template(
            'apache.config',
            self.conf.config_filepath,
            context=self.conf,
            use_sudo=True)
        sudo('a2ensite %(instance_name)s' % self.conf)

push_config = PushConfig()


class PushNginxConfig(PushNginxConfigTask):
    @conf
    def config_template(self):
        return 'nginx_apache.config'

push_nginx_config = PushNginxConfig()
