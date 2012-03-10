import posixpath

from fabric.api import run, sudo, puts, prompt

from . import system, files
from .containers import conf
from .task import Task


__all__ = [
    'add_ppa',
    'install',
    'dump',
    'list_dumps',
    'restore',
    'execute',
    'create_user',
    'drop_user',
    'create_db',
    'drop_db',
    'grant',
    'set_config',
    'set_config_for_django',
    'shell',
    'restart',
    'reload',
]


class AddPpa(Task):
    def do(self):
        sudo('add-apt-repository ppa:pitti/postgresql')

add_ppa = AddPpa()


class Install(Task):
    def do(self):
        system.aptitude_install.run(packages='postgresql libpq-dev')
        sudo('sudo -u %(db_root_user)s '
             'psql '
             '--command="\password %(db_root_user)s" %(db_root_password)s')

install = Install()


class Dump(Task):
    @conf
    def filename(self):
        return '%(db_name)s%(current_time)s.pgc'

    @conf
    def filepath(self):
        return posixpath.join(self.conf.backup_path, self.conf.filename)

    @conf
    def command(self):
        return 'export PGPASSWORD=%(db_password)s;' \
               'pg_dump ' \
               '--host=%(db_host)s ' \
               '--username=%(db_user)s ' \
               '--format=c ' \
               '--file=%(filepath)s' \
               ' %(db_name)s'

    def do(self):
        return run(self.conf.command)

dump = Dump()


class ListDumps(Task):
    def dumps(self):
        dumps = list(files.list_files(self.conf.backup_path))
        dumps.sort(reverse=True)
        return dumps

    def puts(self, dumps):
        for i, dump in enumerate(dumps):
            puts('%s - %s' % (i, posixpath.basename(dump)))

    def do(self):
        self.puts(self.dumps())

list_dumps = ListDumps()


class Restore(Task):
    @conf
    def options(self):
        options = '--clean'
        if self.conf.get('db_renamed'):
            options += ' --no-owner --no-tablespaces --no-privileges'
        return options

    @conf
    def filepath(self):
        if 'filename' not in self.conf:
            with list_dumps.tmp_conf(self.conf):
                dumps = list_dumps.dumps()
                while 1:
                    list_dumps.puts(dumps)
                    number = prompt('Dump number:')
                    try:
                        number = int(number)
                    except ValueError:
                        continue
                    try:
                        self.conf.filename = dumps[number]
                        break
                    except IndexError:
                        continue

        if self.conf.filename.startswith('/'):
            return self.conf.filename
        else:
            return posixpath.join(self.conf.backup_path, self.conf.filename)

    @conf
    def command(self):
        return 'export PGPASSWORD=%(db_password)s;' \
               'pg_restore ' \
               '--host=%(db_host)s ' \
               '--username=%(db_user)s ' \
               '--dbname=%(db_name)s ' \
               '%(options)s ' \
               '%(filepath)s'

    def do(self):
        return run(self.conf.command)

restore = Restore()


class Execute(Task):
    @conf
    def command(self):
        return 'sudo -u %(db_root_user)s psql --command="%(escaped_sql)s"'

    @conf
    def sql():
        raise NotImplementedError()

    @conf
    def escaped_sql(self):
        return self.conf.sql.replace('"', r'\"').strip()

    def do(self):
        return sudo(self.conf.command)

execute = Execute()


class CreateUser(Execute):
    SQL_CREATE_USER = """
    CREATE ROLE %(db_user)s WITH LOGIN PASSWORD '%(db_password)s';
    """.strip()

    @conf
    def sql(self):
        return self.SQL_CREATE_USER

create_user = CreateUser()


class DropUser(Execute):
    SQL_DROP_USER = "DROP ROLE %(db_user)s;"

    @conf
    def sql(self):
        return self.SQL_DROP_USER

drop_user = DropUser()


class CreateDb(Execute):
    SQL_CREATE_DB = """
    CREATE DATABASE %(db_name)s WITH OWNER %(db_user)s;
    """.strip()

    @conf
    def sql(self):
        return self.SQL_CREATE_DB

create_db = CreateDb()


class DropDb(Execute):
    SQL_DROP_DB = "DROP DATABASE %(db_name)s;"

    @conf
    def sql(self):
        return self.SQL_DROP_DB

drop_db = DropDb()


class Grant(Execute):
    SQL_GRANT = """
    GRANT ALL PRIVILEGES ON DATABASE %(db_name)s TO %(db_user)s;
    """.strip()

    @conf
    def sql(self):
        return self.SQL_GRANT

grant = Grant()


class SetConfig(Execute):
    SQL_SET_CONFIG = """
    ALTER ROLE %(db_user)s SET %(name)s = '%(value)s';
    """

    @conf
    def sql(self):
        return self.SQL_SET_CONFIG

set_config = SetConfig()


class SetConfigForDjango(Execute):
    @conf
    def timezone(self):
        return 'UTC'

    def do(self):
        set_config.run(name='client_encoding', value='utf8')
        set_config.run(
            name='default_transaction_isolation', value='read committed')
        set_config.run(name='timezone', value=self.conf.timezone)

set_config_for_django = SetConfigForDjango()


class DbExecute(Execute):
    @conf
    def command(self):
        return 'sudo -u %(db_root_user)s psql %(db_name)s' \
               ' --command="%(escaped_sql)s"'


class Shell(Task):
    @conf
    def do(self):
        run('sudo -u %(db_root_user)s psql' % self.conf)

shell = Shell()


class Restart(Task):
    def do(self):
        sudo('invoke-rc.d postgresql restart')

restart = Restart()


class Reload(Task):
    def do(self):
        sudo('invoke-rc.d postgresql reload')

reload = Reload()
