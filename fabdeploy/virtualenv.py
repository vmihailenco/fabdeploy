import os

from fabric.api import run, sudo

from . import pip
from .containers import conf
from .task import Task
from .utils import inside_virtualenv, inside_project


__all__ = [
    'pip_install',
    'pip_install_req',
    'create',
    'make_relocatable',
    'remove'
]


class PipInstall(pip.Install):
    USE_SUDO = False

    @inside_virtualenv
    def do(self):
        return super(PipInstall, self).do()

pip_install = PipInstall()


class PipInstallReq(PipInstall):
    @conf
    def filepath(self):
        return os.path.join(self.conf.pip_req_lpath, self.conf.pip_req_file)

    @conf
    def options(self):
        options = super(PipInstallReq, self).options()
        options += ' --requirement %(filepath)s' % self.conf
        return options

    @conf
    def app(self):
        return ''

    @inside_project
    def do(self):
        return super(PipInstallReq, self).do()

pip_install_req = PipInstallReq()


class Create(Task):
    @conf
    def options(self):
        return '--no-site-packages --distribute'

    def do(self):
        run('virtualenv %(options)s %(env_path)s' % self.conf)

create = Create()


class MakeRelocatable(Task):
    def do(self):
        run('virtualenv --relocatable %(env_path)s' % self.conf)
        create.run()

make_relocatable = MakeRelocatable()


class Remove(Task):
    def do(self):
        for dirname in ['bin', 'include', 'lib', 'src', 'build']:
            self.conf.dirname = dirname
            sudo('rm --recursive --force %(env_path)s/%(dirname)s' % self.conf)

remove = Remove()
