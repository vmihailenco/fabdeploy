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
def test_example_task_kwargs():
    r = example_task.run(var1='kwarg',
                         var2='kwarg',
                         var3='kwarg',
                         var4='kwarg')
    assert r == ['kwarg', 'kwarg', 'kwarg', 'kwarg']
