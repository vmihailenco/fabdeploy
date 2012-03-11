from nose.tools import with_setup

from fabric.api import env

from fabdeploy.containers import DefaultConf
from fabdeploy.api import Task, conf


class ExampleTask(Task):
    @conf
    def var1(self):
        return 'cls'

    def before_do(self):
        self.conf.setdefault('var1', 'def')
        self.conf.setdefault('var2', 'def')
        self.conf.setdefault('var3', 'def')
        self.conf.setdefault('var4', 'def')

    def do(self):
        return [
            self.conf.var1,
            self.conf.var2,
            self.conf.var3,
            self.conf.var4,
        ]

example_task = ExampleTask()


def setup():
    env.conf = DefaultConf()


def teardown():
    env.conf = DefaultConf()


@with_setup(setup, teardown)
def test_task_has_access_to_env_conf():
    class MyTask(Task):
        pass
    my_task = MyTask()

    env.conf.foo = 'env'
    with my_task.tmp_conf():
        assert my_task.conf.foo == 'env'


@with_setup(setup, teardown)
def test_task_has_access_to_kwargs():
    class MyTask(Task):
        pass
    my_task = MyTask()

    with my_task.tmp_conf(task_kwargs={'foo': 'kwarg'}):
        assert my_task.conf.foo == 'kwarg'


@with_setup(setup, teardown)
def test_task_called_with_conf_of_another_task():
    class Task1(Task):
        @conf
        def var(self):
            return 'task1'
    task1 = Task1()

    class Task0(Task):
        def do(self):
            with task1.tmp_conf(self.conf):
                assert task1.conf.bar == 'task0'

    task0 = Task0()
    task0.run(bar='task0')
