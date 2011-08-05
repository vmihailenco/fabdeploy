import posixpath

from fabric.api import run, sudo, cd

from fabdeploy.containers import conf
from fabdeploy.task import Task
from fabdeploy import pip
from fabdeploy.utils import inside_virtualenv, inside_project


__all__ = ['pip_install', 'pip_install_req', 'create', 'remove']


class PipInstall(pip.Install):
    do = inside_virtualenv(pip.Install.do)

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
            '--download-cache %(pip_cache_path)s ' % self.conf)

pip_install_req = PipInstallReq()


class Create(Task):
    @conf
    def options(self):
        return '--no-site-packages'

    def do(self):
        with cd(posixpath.dirname(self.conf.env_path)):
            run('virtualenv %(options)s %(instance_name)s' % self.conf)

create = Create()


class Remove(Task):
    def do(self):
        for dirname in ['bin', 'include', 'lib', 'src']:
            self.conf.dirname = dirname
            sudo('rm --recursive --force %(env_path)s/%(dirname)s' % self.conf)

remove = Remove()
