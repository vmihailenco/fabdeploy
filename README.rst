Repos
=====

- https://bitbucket.org/vmihailenco/fabdeploy
- https://github.com/vmihailenco/fabdeploy

Quickstart
==========

There is full working example:
https://github.com/vmihailenco/fabdeploy-example.

Create fabconf.py::

    from fabdeploy.api import DefaultConf

    class BaseConf(DefaultConf):
        django_dir = 'project_name'

    class StagingConf(BaseConf):
        address = 'user@staging-host.com'

    class ProdConf(BaseConf):
        address = 'user@prod-host.com'

Create fabfile.py::

    from fabdeploy import monkey; monkey.patch_all()
    from fabric.api import *
    from fabdeploy.api import *; setup_fabdeploy()


    @task
    def user_create():
        users.create.run()
        ssh.push_key.run(pub_key_file='~/.ssh/id_rsa.pub')

    @task
    def deploy():
        pass

Fabdeploy uses two system (linux) users:

- ``sudo_user`` to perform tasks that require sudo right (``root`` by default).
- ``user`` for other tasks (SSH user by default).

In Ubuntu ``root`` user is disabled by default. You can create special
``fabdeploy`` user using following command::

    fab fabd.default_conf:address=user@host,sudo_user=user fabd.create_user

Then you should tell fabdeploy to use new ``sudo_user``::

    class ProdConf(BaseConf):
        sudo_user = 'fabdeploy'

List of available tasks::

    fab --list

List of available variables::

    fab fabd.debug

This is useful to test configuration::

    $ fab fabd.conf:prod fabd.debug:django_path
    /home/prj/src/prj

or::

    $ fab fabd.conf:prod fabd.debug:cpu_count
    2

or::

    $ fab fabd.conf:prod fabd.debug:current_time
    2011.11.27-13.40

To deploy project you may use::

    $ fab fabd.conf:staging deploy
    $ fab fabd.conf:prod deploy

Examples
========

Control where logs are stored
-----------------------------

fabconf.py::

    from fabdeploy.api import DefaultConf

    class ProdConf(DefaultConf):
        my_task__log_path = '/var/log/my_task'

fabfile.py::

    from fabdeploy.api import Task

    class MyTask(Task):
        def do(self):
            print self.conf.log_path

    my_task = MyTask()


Output::

    $ fab fabd.conf:prod my_task
    /var/log/my_task

You can also temporarily set log path::

    $ fab fabd.conf:prod my_task:log_path='/var'
    /var

This works for all variables and all tasks.

Multiple databases
------------------

fabconf.py::

    from fabdeploy.api import DefaultConf

    class ProdConf(DefaultConf):
        # default DB
        db_name = 'name1'
        db_user = 'user1'
        db_password = 'pass1'
        # logging DB
        loggingdb__db_name = 'name2'
        loggingdb__db_user = 'user2'
        loggingdb__db_password = 'pass2'

fabfile.py::

    from fabdeploy import postgres

    @task
    def dump_db():
        postgres.dump.run()  # dump default DB
        postgres.dump.run(_namespace='loggingdb__')  # dump logging DB

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

    from fabdeploy import api
    from fabdeploy.api import DefaultConf

    class DevConf(DefaultConf):
        address = 'user@localhost'
        db = getattr(fabdeploy, 'mysql')

    class ProdConf(DefaultConf):
        address = 'user@localhost'
        db = getattr(fabdeploy, 'postgres')

fabfile.py::

    @task
    def execute():
        print env.conf.db.execute

Configuration
=============

There are some conventions how to configure fabdeploy:

- You should extend DefaultConf::

    from fabdeploy.api import DefaultConf

    class BaseConf(DefaultConf):
        pass

- Each value can contain Python formatting::

    class BaseConf(DefaultConf):
        supervisor__log_dir = '%(var_dir)s/log/supervisor'

- Remote pathes should have posfix ``_path``. You can and should use
  task ``fabd.mkdirs`` to create all remote dirs with one command. It
  will look like this::

    $ fab fabd.conf:staging_conf fabd.mkdirs
    mkdir --parents /path/to/dir1 /path/to/dir2 /path/to/dir3

- Remote dirs (e.g. ``var``) have postfix ``_dir``.

- Local pathes have postfix ``_lpath``. Local dirs have postfix
  ``_ldir``. This is similar to Fabric ``cd`` and ``lcd`` tasks.

- Dirs (postfix ``_dir`` and ``_ldir``) and pathes (postfix ``_path``
  and ``_lpath``) can be Python lists. These lists will be passed to
  ``os.path.join()`` or ``posixpath.join()``. Previous example can
  look like this::

    from fabdeploy.api import DefaultConf

    class BaseConf(DefaultConf):
        supervisor__log_dir = ['%(var_dir)s', 'log', 'supervisor']

- Function can be decorated with conf decorator. For example,
  ``current_time`` task looks like this::

    from fabdeploy.api import DefaultConf

    class BaseConf(DefaultConf):
        @conf
        def current_time(self):
            return datetime.datetime.utcnow().strftime(self.time_format)

  You can use it in your task like this::

    from fabdeploy.api import Task

    class MyTask(Task):
        def do(self):
            puts(self.conf.current_time)

- You can configure each task individually::

    class BaseConf(DefaultConf):
        postgres__db_name = 'postgresql_db'  # module=postres
        mysql__db_name = 'mysql_db'          # module=mysql
        mysql__create_db__db_user = 'root'   # module=mysql, task=create_db

Configuration is stored in task instance variable ``self.conf``. Each
task has its own copy of configuration. Configuration variables are
searched in following places:

- task keyword argument ``var`` (``fab task:foo=bar``);
- task instance method ``var()`` decorated with ``@conf()``;
- key ``var`` in ``env.conf``, which is populated by ``fabd.conf`` task;
- ask user to provide variable ``var`` using fabric prompt.

Global configuration is stored in ``env.conf``.

Writing your task
=================

Your task is class-based fabric class except fabdeploy manages
configuration for you::

    from fabric.api import puts
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

    from fabdeploy import monkey; monkey.patch_all()
    from fabric.api import *
    from fabdeploy.api import *; setup_fabdeploy()

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

        nginx.push_gunicorn_config.run()
        nginx.restart.run()

        supervisor.d()


    @task
    def deploy():
        fabd.mkdirs.run()
        version.create.run()

        postgres.dump.run()

        git.init.run()
        git.push.run()

        supervisor.push_configs.run()
        django.push_settings.run()
        gunicorn.push_config.run()

        virtualenv.create.run()
        virtualenv.pip_install_req.run()
        virtualenv.pip_install.run(app='gunicorn')
        virtualenv.make_relocatable.run()

        django.syncdb.run()
        django.migrate.run()
        django.collectstatic.run()

        version.activate.run()

        supervisor.update.run()
        supervisor.restart_program.run(program='celeryd')
        gunicorn.reload_with_supervisor.run()
