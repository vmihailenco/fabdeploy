import re
import ast

from fabric.api import env, run, sudo, settings, hide
from fabric.utils import puts, abort
from fabric.contrib.files import append

from .containers import conf
from .task import Task


__all__ = [
    'exe_python',
    'cpu_count',
    'os_codename',
    'aptitude_install',
    'setup_backports',
]


class ExePython(Task):
    @conf
    def escaped_code(self):
        return self.conf.code.replace('"', r'\\"')

    def exe(self):
        with settings(hide('everything')):
            output = run('python -c "%(escaped_code)s"' % self.conf)
        return ast.literal_eval(output)

    def do(self):
        r = self.execute()
        puts(r)

exe_python = ExePython()


class CpuCount(ExePython):
    @conf
    def code(self):
        return 'import multiprocessing; print(multiprocessing.cpu_count())'

    def cpu_count(self):
        return self.exe()

    def do(self):
        cpu_count = self.cpu_count()
        puts('Number of CPUs: %s' % cpu_count)

cpu_count = CpuCount()


class OSCodename(ExePython):
    @conf
    def code(self):
        return 'import platform; print(platform.dist())'

    def os_codename(self):
        distname, version, id = self.exe()

        patterns = [
            ('squeeze', ('debian', '^6', '')),
            ('lenny', ('debian', '^5', '')),
            ('natty', ('Ubuntu', '^11.04', '')),
            ('maverick', ('Ubuntu', '^10.10', '')),
            ('lucid', ('Ubuntu', '^10.04', '')),
        ]
        for name, p in patterns:
            if (re.match(p[0], distname) and
                    re.match(p[1], version) and
                    re.match(p[2], id)):
                return name

    def do(self):
        os_codename = self.os_codename()
        if os_codename is None:
            abort('Your OS is unsupported')
            return
        puts('OS codename: %s' % os_codename)

os_codename = OSCodename()


class AptitudeUpdate(Task):
    @conf
    def force(self):
        return False

    def do(self):
        if self.conf.force or not hasattr(env, '_aptitude_updated'):
            sudo('aptitude update')
            env._aptitude_updated = True

aptitude_update = AptitudeUpdate()


class AptitudeInstall(Task):
    @conf
    def options(self):
        return ''

    def do(self):
        aptitude_update.run()
        sudo('aptitude install %(options)s -y %(packages)s' % self.conf)

aptitude_install = AptitudeInstall()


BACKPORTS = {
    'lenny': ('http://backports.debian.org/debian-backports '
              'lenny-backports main contrib non-free'),
    'squeeze': ('http://backports.debian.org/debian-backports '
                'squeeze-backports main contrib non-free'),
    'natty': ('http://archive.ubuntu.com/ubuntu '
              'natty-backports main universe multiverse restricted'),
    'maverick': ('http://archive.ubuntu.com/ubuntu '
                 'maverick-backports main universe multiverse restricted'),
    'lucid': ('http://archive.ubuntu.com/ubuntu '
              'lucid-backports main universe multiverse restricted'),
}


class SetupBackports(Task):
    @conf
    def backports(self):
        if self.conf.os in BACKPORTS:
            return BACKPORTS[self.conf.os]

    def do(self):
        if not self.backports:
            puts('Backports are not available for %(os)s' % self.conf)
            return

        append(
            '/etc/apt/sources.list.d/backports.sources.list',
            'deb %(backports)s' % self.conf,
            use_sudo=True)
        aptitude_update.run(force=True)

setup_backports = SetupBackports()
