import posixpath

from fabric.api import run, sudo

from . import system
from .containers import conf
from .task import Task


__all__ = ['install', 'dump', 'execute', 'create_user', 'drop_user',
           'create_db', 'drop_db', 'grant']


class Install(Task):
    def do(self):
        system.aptitude_install.run(packages='postgresql libpq-dev')
        sudo('sudo -u postgres psql --command="\password postgres" postgres')

install = Install()


class Dump(Task):
    @conf
    def filename(self):
        return '%(db_name)s%(current_time)s.pgc' % self.conf

    @conf
    def filepath(self):
        return posixpath.join(self.conf.backups_path, self.conf.filename)

    @conf
    def command(self):
        return 'export PGPASSWORD=%(db_password)s;' \
               'pg_dump --host=localhost --username=%(db_user)s ' \
               '--format=c --file=%(filepath)s %(db_name)s' % self.conf

    def do(self):
        return run(self.conf.command)

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

    def do(self):
        return sudo(self.conf.command)

execute = Execute()


class CreateUser(Execute):
    SQL_CREATE_USER = """
    CREATE ROLE %(db_user)s WITH LOGIN PASSWORD '%(db_password)s';
    """.strip()

    @conf
    def sql(self):
        return self.SQL_CREATE_USER % self.conf

create_user = CreateUser()


class DropUser(Execute):
    SQL_DROP_USER = "DROP ROLE %(db_user)s;"

    @conf
    def sql(self):
        return self.SQL_DROP_USER % self.conf

drop_user = DropUser()


class CreateDb(Execute):
    SQL_CREATE_DB = """
    CREATE DATABASE %(db_name)s WITH OWNER %(db_user)s;
    """.strip()

    @conf
    def sql(self):
        return self.SQL_CREATE_DB % self.conf

create_db = CreateDb()


class DropDb(Execute):
    SQL_DROP_DB = "DROP DATABASE %(db_name)s;"

    @conf
    def sql(self):
        return self.SQL_DROP_DB % self.conf

drop_db = DropDb()


class Grant(Execute):
    SQL_GRANT = """
    GRANT ALL PRIVILEGES ON DATABASE %(db_name)s TO %(db_user)s;
    """.strip()

    @conf
    def sql(self):
        return self.SQL_GRANT % self.conf

grant = Grant()
