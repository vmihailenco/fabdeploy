import posixpath

from fabric.api import settings, run, sudo, puts, warn, hide

from fabdeploy.containers import conf
from fabdeploy.task import Task
from fabdeploy import system


__all__ = ['install', 'dump', 'execute', 'create_user', 'drop_user',
           'create_db', 'grant', 'drop_db']


class Install(Task):
    """Installs mysql."""

    VERSIONS = {
        'lenny': '5.0',
        'squeeze': '5.1',
        'lucid': '5.1',
        'maverick': '5.1',
    }

    def is_installed(self):
        with settings(warn_only=True):
            output = run('mysql --version')
        return output.succeeded

    def do(self):
        if self.is_installed():
            puts('Mysql is already installed.')
            return

        system.aptitude_install('debconf-utils')

        version = self.versions[self.conf.os]
        debconf_defaults = [
            'mysql-server-%s mysql-server/root_password_again password %s' %
                (version, self.conf.db_root_password),
            'mysql-server-%s mysql-server/root_password password %s' %
                (version, self.conf.db_root_password),
        ]
        sudo('echo "%s" | debconf-set-selections' %
             '\n'.join(debconf_defaults))

        message = ['\n', '=' * 10, '\n',
                   'MySQL root password is "%s"' % self.conf.db_root_password,
                   '\n', '=' * 10, '\n']
        warn(''.join(message))
        system.aptitude_install('mysql-server')

install = Install()


class Dump(Task):
    @conf
    def filename(self):
        return '%(db_name)s%(current_time)s.sql' % self.conf

    @conf
    def filepath(self):
        return posixpath.join(self.conf.backups_path, self.conf.filename)

    def do(self):
        run('mysqldump --user="%(db_user)s" --password="%(db_password)s" '
            '%(db_name)s > %(filepath)s' % self.conf)

dump = Dump()


class Execute(Task):
    @conf
    def escaped_sql(self):
        return self.conf.sql.replace('"', r'\"')

    def do(self):
        return run('echo "%(escaped_sql)s" | mysql --user="%(db_root_user)s" '
                   '--password="%(db_root_password)s"' % self.conf)

execute = Execute()


class CreateUser(Execute):
    SQL_USER_EXISTS = "SHOW GRANTS FOR '%(db_user)s'@localhost;"
    SQL_CREATE_USER = """
    CREATE USER '%(db_user)s'@localhost
    IDENTIFIED BY '%(db_password)s';
    """

    @conf
    def sql_user_exists(self):
        return self.SQL_USER_EXISTS % self.conf

    @conf
    def sql(self):
        return self.SQL_CREATE_USER % self.conf

    def user_exists(self):
        with settings(hide('everything'), warn_only=True):
            with execute.tmp_conf(self.conf):
                result = execute.run(sql=self.conf.sql_user_exists)
        return result.succeeded

    def do(self):
        if self.user_exists():
            puts('MySQL user "%(db_user)s" already exists' % self.conf)
            return
        super(CreateUser, self).do()

create_user = CreateUser()


class DropUser(Execute):
    SQL_DROP_USER = "DROP USER '%(db_user)s'@localhost;"

    @conf
    def sql(self):
        return self.SQL_DROP_USER % self.conf

drop_user = DropUser()


class CreateDb(Execute):
    SQL_CREATE_DB = """
    CREATE DATABASE %(db_name)s
    DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
    """.strip()

    @conf
    def sql(self):
        return self.SQL_CREATE_DB % self.conf

create_db = CreateDb()


class Grant(Execute):
    SQL_GRANT = """
    GRANT ALL ON %(db_name)s.* TO '%(db_user)s'@'localhost';
    FLUSH PRIVILEGES;
    """.strip()

    @conf
    def sql(self):
        return self.SQL_GRANT % self.conf

grant = Grant()


class DropDb(Execute):
    SQL_DROP_DB = "DROP DATABASE %(db_name)s;"

    @conf
    def sql(self):
        return self.SQL_DROP_DB % self.conf

drop_db = DropDb()
