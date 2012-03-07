import re
import posixpath

from fabric.api import cd, run, sudo, settings
from fabric.contrib import files

from . import pip
from .containers import conf
from .task import Task as BaseTask
from .utils import upload_config_template, upload_init_template


__all__ = [
    'install',
    'push_init_config',
    'start',
    'stop',
    'd',
    'ctl',
    'shutdown',
    'update',
    'reload',
    'push_d_config',
    'push_configs',
    'start_program',
    'stop_program',
    'restart_program',
    'pid_program',
]


class Task(BaseTask):
    @conf
    def supervisor_config_path(self):
        return posixpath.join(self.conf.etc_path, 'supervisor')


class Install(Task):
    def do(self):
        pip.install.run(app='supervisor', upgrade=True)

install = Install()


class PushInitConfig(Task):
    def do(self):
        upload_init_template('supervisord.conf', use_sudo=True)

push_init_config = PushInitConfig()


class Start(Task):
    def do(self):
        sudo('start supervisord')

start = Start()


class Stop(Task):
    def do(self):
        sudo('stop supervisord')

stop = Stop()


class D(Task):
    def do(self):
        with settings(warn_only=True):
            sudo('supervisord --configuration=%(supervisord_config_file)s' %
                 self.conf)

d = D()


class Ctl(Task):
    """Perform ``command`` or show supervisor console."""

    @conf
    def command(self):
        return self.conf.get('command', '')

    def do(self):
        return sudo(
            'supervisorctl --configuration=%(supervisord_config_file)s '
             '%(command)s' % self.conf)

ctl = Ctl()


class Shutdown(Ctl):
    """Shutdown supervisord."""

    @conf
    def command(self):
        return 'shutdown'

shutdown = Shutdown()


class Update(Ctl):
    @conf
    def command(self):
        return 'update'

update = Update()


class Reload(Ctl):
    @conf
    def command(self):
        return 'reload'

reload = Reload()


class PushDConfig(Task):
    def do(self):
        if 'supervisord_config_lfile' in self.conf:
            upload_config_template(
                self.conf.supervisord_config_lfile,
                self.conf.supervisord_config_file,
                context=self.conf)

push_d_config = PushDConfig()


class PushConfigs(Task):
    """Push configs for ``supervisor_programs``."""

    @conf
    def configs_glob(self):
        return '    %(active_etc_link)s/supervisor/*.conf'

    def do(self):
        with cd(self.conf.supervisor_config_path):
            # force is needed when folder is empty
            run('rm --force *.conf')

        push_d_config.run()

        for program in self.conf.supervisor_programs:
            config = '%s.conf' % program
            from_filepath = 'supervisor/%s' % config
            to_filepath = posixpath.join(
                self.conf.supervisor_config_path,
                config)
            upload_config_template(
                from_filepath,
                to_filepath,
                context=self.conf)

        files.append(
            self.conf.supervisord_config_file,
            self.conf.configs_glob,
            use_sudo=True)

push_configs = PushConfigs()


class ProgramCommand(Task):
    def get_command(self, program):
        self.conf._program = program
        return '%(command)s %(supervisor_prefix)s%(_program)s' % self.conf

    def do(self):
        if 'program' in self.conf and self.conf.program:
            return ctl.run(command=self.get_command(self.conf.program))

        for program in self.conf.supervisor_programs:
            ctl.run(command=self.get_command(program))

    def run(self, program='', **kwargs):
        return super(ProgramCommand, self).run(program=program, **kwargs)


class RestartProgram(ProgramCommand):
    """Restart ``supervisor_programs``."""

    @conf
    def command(self):
        return 'restart'

restart_program = RestartProgram()


class StartProgram(ProgramCommand):
    """Start ``supervisor_programs``."""

    @conf
    def command(self):
        return 'start'

start_program = StartProgram()


class StopProgram(ProgramCommand):
    """Stop ``supervisor_programs``."""

    @conf
    def command(self):
        return 'stop'

stop_program = StopProgram()


class PidProgram(ProgramCommand):
    @conf
    def command(self):
        return 'status'

    def do(self):
        output = super(PidProgram, self).do()
        m = re.search(r'pid\s(\d+)', output)
        if m:
            return m.group(1)
        else:
            return 0

pid_program = PidProgram()
