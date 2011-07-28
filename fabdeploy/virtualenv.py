import posixpath

from fabric.api import run, sudo, cd

from fabdeploy.containers import conf
from fabdeploy.task import Task
from fabdeploy.utils import inside_virtualenv, inside_project, run_as_sudo


__all__ = ['pip_install', 'pip_install_req', 'create', 'remove']


class PipInstall(Task):
    def before_do(self):
        self.conf.setdefault('upgrade', False)

    @conf
    def options(self):
        options = self.conf.get('options', '')
        if self.conf.upgrade:
            options += ' --upgrade'
        return options

    @run_as_sudo
    def do(self):
        sudo('pip install %(options)s '
            '--download-cache %(pip_cache_dir)s '
            '%(app)s' % self.conf)

pip_install = PipInstall()


class PipInstallReq(PipInstall):
    @conf
    def filepath(self):
        return self.conf.pip_req_path_getter(self.conf.pip_req_name)

    @conf
    def options(self):
        options = super(PipInstallReq, self).options()
        options += ' --requirement %(filepath)s' % self.conf
        return options

    @inside_project
    @inside_virtualenv
    def do(self):
        run('pip install %(options)s '
            '--download-cache %(pip_cache_dir)s ' % self.conf)

pip_install_req = PipInstallReq()


class Create(Task):
    @conf
    def options(self):
        return '--no-site-packages'

    def do(self):
        with cd(posixpath.dirname(self.conf.env_dir)):
            run('virtualenv %(options)s %(instance_name)s' % self.conf)

create = Create()


class Remove(Task):
    @run_as_sudo
    def do(self):
        for dirname in ['bin', 'include', 'lib', 'src']:
            self.conf.dirname = dirname
            sudo('rm --recursive --force %(env_dir)s/%(dirname)s' % self.conf)

remove = Remove()
