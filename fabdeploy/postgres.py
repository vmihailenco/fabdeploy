import posixpath

from fabric.api import sudo

from fabdeploy.containers import conf
from fabdeploy.task import Task
from fabdeploy.utils import run_as_sudo


__all__ = ['dump', 'create_role', 'grant', 'create_db', 'drop_db']


class Dump(Task):
    @conf
    def filename(self):
        return '%(db_name)s%(current_time)s.pgc' % self.conf

    @conf
    def filepath(self):
        return posixpath.join(self.conf.backups_path, self.conf.filename)

    @conf
    def command(self):
        return 'pg_dump --host=localhost --username=%(db_user)s ' \
               '--format=c --file=%(filepath)s %(db_name)s' % self.conf

    @run_as_sudo
    def do(self):
        return sudo(self.conf.command)

dump = Dump()


class Execute(Task):
    @conf
    def command(self):
        return ('sudo -u %(db_root_user)s psql --command="%(escaped_sql)s"' %
                self.conf)

    @conf
    def sql():
        raise NotImplementedError()

    @conf
    def escaped_sql(self):
        return self.conf.sql.replace('"', r'\"')

    @run_as_sudo
    def do(self):
        return sudo(self.conf.command)

execute = Execute()


class CreateRole(Execute):
    SQL_CREATE_ROLE = """
    CREATE ROLE %(db_user)s WITH LOGIN PASSWORD '%(db_password)s';
    """.strip()

    @conf
    def sql(self):
        return self.SQL_CREATE_ROLE % self.conf

create_role = CreateRole()


class Grant(Execute):
    SQL_GRANT = """
    GRANT ALL PRIVILEGES ON DATABASE %(db_name)s TO %(db_user)s;
    """.strip()

    @conf
    def sql(self):
        return self.SQL_GRANT % self.conf

grant = Grant()


class CreateDb(Execute):
    SQL_CREATE_DB = """
    CREATE DATABASE %(db_name)s WITH OWNER %(db_user)s;
    """.strip()

    @conf
    def sql(self):
        return self.SQL_CREATE_DB % self.conf

create_db = CreateDb()


class DropDb(Execute):
    SQL_DROP_DB = """
    DROP DATABASE %(db_name)s;
    """.strip()

    @conf
    def sql(self):
        return self.SQL_DROP_DB % self.conf

drop_db = DropDb()
