from fabric.api import sudo, settings

from .containers import conf
from .task import Task as BaseTask
from .utils import upload_config_template


__all__ = ['install', 'd', 'ctl', 'shutdown', 'update', 'push_configs',
           'start_program', 'stop_program', 'restart_program']


class Task(BaseTask):
    pass


class Install(Task):
    def do(self):
        sudo('pip install --upgrade supervisor')

install = Install()


class D(Task):
    def do(self):
        with settings(warn_only=True):
            sudo('supervisord --configuration=%(supervisord_config)s' % self.conf)

d = D()


class Ctl(Task):
    """Perform ``command`` or show supervisor console."""

    @conf
    def command(self):
        return self.conf.get('command', '')

    def do(self):
        sudo('supervisorctl --configuration=%(supervisord_config)s '
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


class PushConfigs(Task):
    """Push configs for ``supervisor_programs``."""

    def do(self):
        if 'supervisord_config_template' in self.conf:
            upload_config_template(self.conf.supervisord_config_template,
                                   self.conf.supervisord_config,
                                   context=self.conf)

        for program in self.conf.supervisor_programs:
            config = '%s.conf' % program
            from_filepath = 'supervisor/%s' % config
            to_filepath = '%s/%s' % (self.conf.supervisor_config_path,
                                     config)
            upload_config_template(from_filepath,
                                   to_filepath,
                                   context=self.conf)

push_configs = PushConfigs()


class ProgramCommand(Task):
    def get_command(self, program):
        self.conf.program = program
        return '%(command)s %(supervisor_prefix)s%(program)s' % self.conf

    def do(self):
        if 'program' in self.conf and self.conf.program:
            ctl.run(command=self.get_command(self.conf.program))
            return

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
