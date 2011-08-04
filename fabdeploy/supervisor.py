from fabric.api import sudo, settings

from fabdeploy.containers import conf
from fabdeploy.task import Task as BaseTask
from fabdeploy.utils import run_as_sudo, upload_config_template


__all__ = ['install', 'd', 'ctl', 'shutdown', 'push_configs',
           'stop_programs', 'restart_programs']


class Task(BaseTask):
    pass


class Install(Task):
    @run_as_sudo
    def do(self):
        sudo('pip install --upgrade supervisor')

install = Install()


class D(Task):
    @run_as_sudo
    def do(self):
        with settings(warn_only=True):
            sudo('supervisord --configuration=%(supervisord_config)s' % self.conf)

d = D()


class Ctl(Task):
    def before_do(self):
        super(Ctl, self).before_do()
        self.conf.setdefault('command', '')

    @run_as_sudo
    def do(self):
        sudo('supervisorctl --configuration=%(supervisord_config)s '
             '%(command)s' % self.conf)

ctl = Ctl()


class Shutdown(Ctl):
    @conf
    def command(self):
        return 'shutdown'

shutdown = Shutdown()


class PushConfigs(Task):
    def do(self):
        if 'supervisord_config_template' in self.conf:
            upload_config_template(self.conf.supervisord_config_template,
                                   self.conf.supervisord_config,
                                   context=self.conf)

        for _, _, programs in self.conf.supervisor_programs:
            for program in programs:
                config = '%s.conf' % program
                from_filepath = 'supervisor/%s' % config
                to_filepath = '%s/%s' % (self.conf.supervisor_config_path,
                                         config)
                upload_config_template(from_filepath,
                                       to_filepath,
                                       context=self.conf)

push_configs = PushConfigs()


class ProgramsCommand(Task):
    def get_group_command(self, group):
        self.conf.group = group
        return '%(command)s %(supervisor_prefix)s%(group)s:' % self.conf

    def get_program_command(self, program):
        self.conf.program = program
        return '%(command)s %(supervisor_prefix)s%(program)s' % self.conf

    def do(self):
        for _, group, programs in self.conf.supervisor_programs:
            if group:
                ctl.run(command=self.get_group_command(group))
                continue
            for program in programs:
                ctl.run(command=self.get_program_command(program))


class RestartPrograms(ProgramsCommand):
    @conf
    def command(self):
        return 'restart'

restart_programs = RestartPrograms()


class StopPrograms(ProgramsCommand):
    @conf
    def command(self):
        return 'stop'

stop_programs = StopPrograms()
