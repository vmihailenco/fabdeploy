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
    'get_release',
    'list_releases',
    'work_on',
    'purge_old',
    'purge_tmp',
    'purge',
]


class Exists(Task):
    def do(self):
        return files.exists(self.conf.release_path)

exists = Exists()


class Create(Task):
    def do(self):
        if files.exists(posixpath.join(self.conf.env_path, 'bin')):
            puts('Release %(release)s already exists... skipping...' %
                 self.conf)
            return

        if not self.conf.get('fresh', False) and \
           files.exists(self.conf.last_env_link):
            run('cp --recursive %(last_env_link)s %(release_path)s' %
                self.conf)

create = Create()


class Activate(Task):
    def do(self):
        # save previous release
        run('rm --force %(previous_release_link)s' % self.conf)
        if files.exists(self.conf.last_release_link):
            run('cp '
                '--no-dereference '
                '--preserve=links '
                '%(last_release_link)s %(previous_release_link)s' % self.conf)

        # save last release
        run('ln '
            '--symbolic '
            '--force '
            '--no-target-directory '
            '%(release_path)s '
            '%(last_release_link)s' % self.conf)

        # activate current release
        run('ln '
            '--symbolic '
            '--force '
            '--no-target-directory '
            '%(release_path)s %(current_release_link)s' % self.conf)

        run('touch %(release_data_file)s' % self.conf)

activate = Activate()


class ListReleases(Task):
    def releases(self):
        releases = []
        for file in list_files(self.conf.home_path):
            name = posixpath.basename(file)
            try:
                datetime.datetime.strptime(name, self.conf.time_format)
            except ValueError:
                continue

            f = posixpath.join(self.conf.home_path, name, '.fabdeploy')
            is_tmp = not files.exists(f)
            releases.append((name, is_tmp))

        releases.sort(reverse=True)
        return releases

    def puts(self, releases):
        for i, (release, is_tmp) in enumerate(releases):
            if is_tmp:
                s = '%s - %s (tmp)'
            else:
                s = '%s - %s'
            puts(s % (i, posixpath.basename(release)))

    def do(self):
        self.puts(self.releases())

list_releases = ListReleases()


class GetRelease(Task):
    def release(self, name):
        name = '%s_release_link' % name
        if name not in self.conf:
            raise ValueError
        link = getattr(self.conf, name)
        if not files.exists(link):
            raise ValueError
        return posixpath.basename(run('readlink ' + link))

    def do(self):
        try:
            release = self.release(self.conf.release_name)
            puts('%s release: %s' % (self.conf.release_name, release))
        except ValueError:
            puts('Release %s does not exits' % self.conf.release_name)

    def run(self, release_name, **kwargs):
        kwargs.setdefault('release_name', release_name)
        return super(GetRelease, self).run(**kwargs)

get_release = GetRelease()


class WorkOn(Task):
    def release(self):
        with list_releases.tmp_conf(self.conf):
            releases = list_releases.releases()

            number = self.conf.get('release_id', None)
            while 1:
                if number is None:
                    list_releases.puts(releases)
                    number = prompt('Release number:')

                with get_release.tmp_conf(self.conf):
                    try:
                        return get_release.release(number)
                    except ValueError:
                        pass

                try:
                    number = int(number)
                except ValueError:
                    number = None
                    continue

                try:
                    return releases[number]
                except (IndexError, TypeError):
                    number = None
                    continue

        raise NotImplementedError()

    def do(self):
        release = self.release()
        self.conf.set_globally('release', release[0])

    def run(self, release_id=None, **kwargs):
        if release_id is not None:
            kwargs.setdefault('release_id', release_id)
        return super(WorkOn, self).run(**kwargs)

work_on = WorkOn()


class PurgeTask(Task):
    def purge_confirmed(self, releases):
        puts('We are going to purge following releases: %s' %
             ', '.join(releases))
        answer = prompt('Do you want to continue? (y/n)').lower()
        if answer in ('y', 'yes'):
            return True
        else:
            return False

    def purge(self, releases):
        dirs = []
        for v in releases:
            dirs.append(posixpath.join(self.conf.home_path, v))
        run('rm --recursive --force ' + ' '.join(dirs))


class PurgeTmp(PurgeTask):
    def do(self):
        with list_releases.tmp_conf(self.conf):
            releases = list_releases.releases()

        tmp_releases = [v for v, is_tmp in releases if is_tmp]
        if not tmp_releases:
            puts('There is no tmp releases - nothing to purge...')
            return

        if self.purge_confirmed(tmp_releases):
            self.purge(tmp_releases)

purge_tmp = PurgeTmp()


class PurgeOld(PurgeTask):
    @conf
    def keep_number(self):
        return 5

    def do(self):
        with list_releases.tmp_conf(self.conf):
            releases = list_releases.releases()

        old_releases = [v for v, is_tmp in releases if not is_tmp]
        if len(old_releases) <= self.conf.keep_number:
            puts('There are only %s releases available - nothing to purge...' %
                 len(old_releases))
            return

        old_releases = old_releases[self.conf.keep_number:]
        if self.purge_confirmed(old_releases):
            self.purge(old_releases)

purge_old = PurgeOld()


class Purge(Task):
    def do(self):
        purge_tmp.run()
        purge_old.run()

purge = Purge()
