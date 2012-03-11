import os

from fabric.api import local, run, put, lcd, cd

from .containers import conf
from .task import Task


__all__ = ['push', 'push_files']


class PushTask(Task):
    @conf
    def src_file(self):
        if 'src_file' not in self.conf:
            self.conf.src_file = \
                '/tmp/fabdeploy_%(current_time)s.tar' % self.conf
        return self.conf.src_file

    @conf
    def target_file(self):
        if 'target_file' not in self.conf:
            self.conf.target_file = \
                '%(target_path)s/fabdeploy_%(current_time)s.tar' % self.conf
        return self.conf.target_file


class Push(PushTask):
    @conf
    def exclude_string(self):
        excludes = ['*.pyc', '*.pyo']
        exclude_string = ' '.join(['--exclude "%s"' % pattern
                                   for pattern in excludes])

        if os.path.exists('%(src_path)s/.excludes' % self.conf):
            exclude_string = '--exclude-from .excludes ' + exclude_string

        return exclude_string

    def do(self):
        local('tar %(exclude_string)s '
              '--create '
              '--gzip '
              '--file %(src_file)s '
              '--directory %(src_path)s .' % self.conf)
        put(self.conf.src_file, self.conf.target_file)
        local('rm %(src_file)s' % self.conf)
        with cd(self.conf.target_path):
            run('tar '
                '--extract '
                '--gunzip '
                '--file %(target_file)s' % self.conf)
            run('rm %(target_file)s' % self.conf)

push = Push()


class PushFiles(PushTask):
    def do(self):
        if isinstance(self.conf.files, list):
            files = self.conf.files
        else:
            files = [f.strip() for f in self.conf.files.split(',')]
        self.conf._files = '--add-file ' + '--add-file '.join(files)

        with lcd(self.conf.src_path):
            local(
                'tar '
                '--create '
                '--gzip '
                '--file %(src_file)s '
                '%(_files)s' % self.conf)
        put(self.conf.src_file, self.conf.target_file)
        local('rm %(src_file)s' % self.conf)
        with cd(self.conf.target_path):
            run('tar '
                '--extract '
                '--gunzip '
                '--file %(target_file)s' % self.conf)
            run('rm %(target_file)s' % self.conf)

push_files = PushFiles()
