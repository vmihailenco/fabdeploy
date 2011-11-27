from nose.tools import with_setup

from fabric.api import env

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
    env.conf = {}


def teardown():
    env.conf = {}


@with_setup(setup, teardown)
def test_example_task_defaults():
    r = example_task.run()
    assert r == ['cls', 'def', 'def', 'def']


@with_setup(setup, teardown)
def test_example_task_with_env():
    env.conf = {'var2': 'env'}
    r = example_task.run(var3='kwarg')
    assert r == ['cls', 'env', 'kwarg', 'def']


@with_setup(setup, teardown)
def test_example_task_with_kwargs():
    r = example_task.run(
        var1='kwarg',
        var2='kwarg',
        var3='kwarg',
        var4='kwarg')
    assert r == ['kwarg', 'kwarg', 'kwarg', 'kwarg']


class Task1(Task):
    @conf
    def var(self):
        return 'task1'

    def do(self):
        return self.conf.var

task1 = Task1()


class Task2(Task):
    def do(self):
        with task1.tmp_conf(self.conf):
            return task1.run()

task2 = Task2()


@with_setup(setup, teardown)
def test_task_called_with_conf_of_another_task():
    assert task2.run(var='foo') == 'foo'


class Task3(Task):
    def do(self):
        return task1.run(var='bar')

task3 = Task3()


@with_setup(setup, teardown)
def test_task_called_from_another_task():
    assert task3.run(var='foo') == 'bar'


class Task4(Task):
    def do(self):
        with task1.tmp_conf({'var': 'task4'}):
            v1 = task1.run()
        v2 = task1.run()
        return v1, v2, self.conf.var

task4 = Task4()


@with_setup(setup, teardown)
def test_task_with_different_configs():
    r = task4.run(var='foo')
    assert r == ('task4', 'task1', 'foo')
