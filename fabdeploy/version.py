import datetime
import posixpath

from fabric.api import run, puts, prompt
from fabric.contrib import files

from .files import list_files
from .containers import conf
from .task import Task


__all__ = [
    'exists',
    'create',
    'activate',
    'get_version',
    'list_versions',
    'work_on',
    'purge_old',
    'purge_tmp',
    'purge',
]


class Exists(Task):
    def do(self):
        return files.exists(self.conf.version_path)

exists = Exists()


class Create(Task):
    def do(self):
        if files.exists(posixpath.join(self.conf.env_path, 'bin')):
            puts('Version %(version)s already exists... skipping...' %
                 self.conf)
            return

        if not self.conf.get('fresh', False) and \
           files.exists(self.conf.last_env_link):
            run('cp --recursive %(last_env_link)s %(version_path)s' %
                self.conf)

create = Create()


class Activate(Task):
    def do(self):
        # save previous version
        run('rm --force %(previous_version_link)s' % self.conf)
        if files.exists(self.conf.last_version_link):
            run('cp '
                '--no-dereference '
                '--preserve=links '
                '%(last_version_link)s %(previous_version_link)s' % self.conf)

        # save last version
        run('ln '
            '--symbolic '
            '--force '
            '--no-target-directory '
            '%(version_path)s '
            '%(last_version_link)s' % self.conf)

        # activate current version
        run('ln '
            '--symbolic '
            '--force '
            '--no-target-directory '
            '%(version_path)s %(active_version_link)s' % self.conf)

        run('touch %(version_data_file)s' % self.conf)

activate = Activate()


class ListVersions(Task):
    def versions(self):
        versions = []
        for file in list_files(self.conf.home_path):
            name = posixpath.basename(file)
            try:
                datetime.datetime.strptime(name, self.conf.time_format)
            except ValueError:
                continue

            f = posixpath.join(self.conf.home_path, name, '.fabdeploy')
            is_tmp = not files.exists(f)
            versions.append((name, is_tmp))

        versions.sort(reverse=True)
        return versions

    def puts(self, versions):
        for i, (version, is_tmp) in enumerate(versions):
            if is_tmp:
                s = '%s - %s (tmp)'
            else:
                s = '%s - %s'
            puts(s % (i, posixpath.basename(version)))

    def do(self):
        self.puts(self.versions())

list_versions = ListVersions()


class GetVersion(Task):
    def version(self, name):
        name = '%s_version_link' % name
        if name not in self.conf:
            raise ValueError
        link = getattr(self.conf, name)
        if not files.exists(link):
            raise ValueError
        return posixpath.basename(run('readlink ' + link))

    def do(self):
        try:
            version = self.version(self.conf.version_name)
            puts('%s version: %s' % (self.conf.version_name, version))
        except ValueError:
            puts('Version %s does not exits' % self.conf.version_name)

    def run(self, version_name, **kwargs):
        kwargs.setdefault('version_name', version_name)
        return super(GetVersion, self).run(**kwargs)

get_version = GetVersion()


class WorkOn(Task):
    def version(self):
        with list_versions.tmp_conf(self.conf):
            versions = list_versions.versions()

            number = self.conf.get('version_id', None)
            while 1:
                if number is None:
                    list_versions.puts(versions)
                    number = prompt('Version number:')

                with get_version.tmp_conf(self.conf):
                    try:
                        return get_version.version(number)
                    except ValueError:
                        pass

                try:
                    number = int(number)
                except ValueError:
                    number = None
                    continue

                try:
                    return versions[number]
                except (IndexError, TypeError):
                    number = None
                    continue

        raise NotImplementedError()

    def do(self):
        version = self.version()
        self.conf.set_globally('version', version[0])

    def run(self, version_id=None, **kwargs):
        if version_id is not None:
            kwargs.setdefault('version_id', version_id)
        return super(WorkOn, self).run(**kwargs)

work_on = WorkOn()


class PurgeTask(Task):
    def purge_confirmed(self, versions):
        puts('We are going to purge following versions: %s' %
             ', '.join(versions))
        answer = prompt('Do you want to continue? (y/n)').lower()
        if answer in ('y', 'yes'):
            return True
        else:
            return False

    def purge(self, versions):
        dirs = []
        for v in versions:
            dirs.append(posixpath.join(self.conf.home_path, v))
        run('rm --recursive --force ' + ' '.join(dirs))


class PurgeTmp(PurgeTask):
    def do(self):
        with list_versions.tmp_conf(self.conf):
            versions = list_versions.versions()

        tmp_versions = [v for v, is_tmp in versions if is_tmp]
        if not tmp_versions:
            puts('There is no tmp versions - nothing to purge...')
            return

        if self.purge_confirmed(tmp_versions):
            self.purge(tmp_versions)

purge_tmp = PurgeTmp()


class PurgeOld(PurgeTask):
    @conf
    def keep_number(self):
        return 5

    def do(self):
        with list_versions.tmp_conf(self.conf):
            versions = list_versions.versions()

        old_versions = [v for v, is_tmp in versions if not is_tmp]
        if len(old_versions) <= self.conf.keep_number:
            puts('There are only %s versions available - nothing to purge...' %
                 len(old_versions))
            return

        old_versions = old_versions[self.conf.keep_number:]
        if self.purge_confirmed(old_versions):
            self.purge(old_versions)

purge_old = PurgeOld()


class Purge(Task):
    def do(self):
        purge_tmp.run()
        purge_old.run()

purge = Purge()
