Quickstart
==========

There is full working example: https://github.com/vladimir-webdev/fabdeploy-example.

Create fabconf.py::

    STAGING_CONF = {}
    PROD_CONF = {}

Create fabfile.py::

    from fabdeploy import monkey; monkey.patch_all()
    from fabric.api import *
    from fabdeploy.api import *; setup_fabdeploy()


    @task
    def staging():
        fabconf('staging')


    @task
    def prod():
        fabconf('prod')


    @task
    def deploy():
        pass

List of available tasks::

    fab --list

List of available variables::

    fab fabd.debug

This is useful to test configuration::

    $ fab prod.fabd.debug:django_path
    /home/prj/src/prj

or::

    $ fab prod fabd.debug:cpu_count
    2

or::

    $ fab prod fabd.debug:current_time
    2011.11.27-13.40

Examples
========

Control where logs are stored
-----------------------------

fabconf.py::

    PROD_CONF = {
        'my_task.log_path': '/var/log/my_task',
    }

fabfile.py::

    @task
    def prod():
        fabconf('prod')


    class MyTask(Task):
        def do(self):
            print self.conf.log_path

    my_task = MyTask()


Output::

    $ fab prod my_task
    /var/log/my_task

You can also temporarily set log path::

    $ fab prod my_task:log_path='/var'
    /var

This works for all variables and all tasks.

Built-in tasks customization
----------------------------

Fabdeploy is written to be highly configurable. For example, there is
built-in ``tar`` task, which by default packs whole project, uploads it
to server and unpacks it there.

But you can freely use it to upload custom dirs::

     from fabdeploy import tar

     @task
     def push_static():
         tar.push.run(
             src_dir=os.path.join(env.conf.django_ldir, 'static'),
             target_dir=posixpath.join(env.conf.django_dir, 'static'))

Different DBs for development and production
--------------------------------------------

fabconf.py::

    DEV_CONF = {
        'address': 'user@localhost',
        'db': 'mysql',
    }


    PROD_CONF = {
        'address': 'user@localhost',
        'db': 'postgres',
    }

fabfile.py::

    @task
    def dev():
        fabconf('dev')
        env.conf.db = getattr(fabdeploy, env.conf.db)


    @task
    def prod():
        fabconf('prod')
        env.conf.db = getattr(fabdeploy, env.conf.db)


    @task
    def execute():
        print env.conf.db.execute

Executing tasks
===============

You can pass arguments to tasks using following ways:

- Call ``setup_fabdeploy()`` to setup empty configuration and host ``$USER@localhost``. You will be prompted for any missing variable (once per task)::

    from fabdeploy.api import setup_fabdeploy
    setup_fabdeploy()

- Pass global configuration to ``setup_conf()``::

    from fabdeploy.api import setup_conf

    @task
    def staging():
        env.conf = setup_conf(dict(
            address='user@host',
            db_name='mydb',
            db_user='myuser'
        ))
        env.hosts = [env.address]

  Then tasks can be runned without arguments::

    fab staging postgres.create_db

- Pass arguments directly to task::

    fab staging postgres.create_db:db_name=mydb,db_user=myuser

Configuration
=============

There are some conventions how to configure fabdeploy:

- You should use Python OrderedDict, because often order is important::

    from collections import OrderedDict

    BASE_CONF = OrderedDict([
        ('sudo_user', 'fabdeploy'),
    ])

- Each value can contain Python formatting::

    BASE_CONF = OrderedDict([
        ('supervisor.log_dir', '%(log_dir)s/supervisor'),
    ])

- Remote dirs should have posfix ``_dir``. You can and should use task ``fabd.mkdirs`` to create all remote dirs with one command. It will look like this::

    $ fab fabd.mkdirs
    mkdir --parents /path/to/dir1 /path/to/dir2 /path/to/dir3

- Local dirs have postfix ``_ldir`` (similar to Fabric ``cd`` and ``lcd``).

- Dirs (postfix ``_dir`` and ``_ldir``) and pathes (postfix ``_path`` and ``_lpath``) can be lists. This list will be passed to ``os.path.join()`` or ``posixpath.join()``. Previous example can look like this::

    BASE_CONF = OrderedDict([
        ('supervisor.log_dir', ['%(log_dir)s', 'supervisor']),
    ])

- You can configure each task individually::

    BASE_CONF = OrderedDict([
        ('postgres.db_name', 'postgresql_db'), # module=postres
        ('mysql.db_name', 'mysql_db'),         # module=mysql
        ('mysql.create_db.db_user', 'root'),   # module=mysql, task=create_db
    ])

Configuration is stored in task instance variable ``self.conf``. Each task has its own copy of configuration. Configuration variables are searched in following places:

- task keyword argument ``var`` (``fab task:foo=bar``);
- task instance method ``var()`` decorated with ``@conf()``;
- key ``var`` in ``env.conf`` dict;
- ask user to provide variable ``var`` using fabric prompt.

Writing your task
=================

Your task is class-based fabric class except fabdeploy manages configuration for you::

    from fabdeploy.api import Task, conf

    class MessagePrinter(Task):
        @conf
        def message(self):
            if 'message' in self.conf:
                return self.conf.message
            return 'Hi!'

        def do(self):
            if self.conf.secret == '123':
                puts(self.conf.message)
            else:
                puts('huh?')

    message_printer = MessagePrinter()

Then you can run this task like this::

    $ fab message_printer
    > secret = 123
    Hi!
    $ fab message_printer:message='Hello world!'
    > secret = 123
    Hello world!

Fabfile example
===============

Typical fabfile may look like this::

    from collections import OrderedDict
    from fabric.api import task, settings
    from fabdeploy.api import *


    setup_fabdeploy()

    BASE_CONF = OrderedDict(
       ('django_dir', 'projectname'),
       ('supervisor_programs', [
           (1000, 'group', ['gunicorn'])
       ])
    )


    @task
    def prod():
        conf = BASE_CONF.copy()
        conf['address'] = 'user@prodhost.com'
        env.conf = setup_conf(conf)
        env.hosts = [env.conf.address]


    @task
    def install():
        users.create.run()
        ssh.push_key.run(pub_key_file='~/.ssh/id_rsa.pub')

        system.setup_backports.run()
        system.install_common_software.run()

        with settings(warn_only=True):
            postgres.create_role.run()
            postgres.create_db.run()
            postgres.grant.run()

        nginx.install.run()

        for app in ['supervisor']:
            pip.install.run(app=app)


    @task
    def setup():
        fabd.mkdirs.run()

        gunicorn.push_config.run()
        nginx.push_gunicorn_config.run()
        nginx.restart.run()


    @task
    def deploy():
        fabd.mkdirs.run()
        postgres.dump.run()

        git.init.run()
        git.push.run()
        django.push_settings.run()
        supervisor.push_configs.run()

        virtualenv.create.run()
        virtualenv.pip_install.run(app='gunicorn')

        django.syncdb.run()
        django.migrate.run()
        django.collectstatic.run()

        supervisor.d.run()
        supervisor.restart_programs.run()
