from jinja2 import Template

from fabdeploy.task import Task
from fabdeploy.containers import BaseConf, conf


def test_set_get():
    c = BaseConf()
    c.foo = 'data'
    assert c.foo == 'data'


def test_get_from_task():
    class MyTask(Task):
        @conf
        def foo(self):
            return 'task'

    c = BaseConf(tasks=[MyTask()])
    c.foo = 'user'
    assert c.foo == 'task'

    c.setdefault('foo', 'bla')
    assert c.foo == 'task'

    c.setdefault('bar', 'default')
    assert c.bar == 'default'

    assert c.get('not_exist', 'default') == 'default'


def test_get_from_multiple_tasks():
    class Task1(Task):
        @conf
        def foo(self):
            return 'task1'

    class Task2(Task):
        @conf
        def foo(self):
            return 'task1'

    c = BaseConf(tasks=[Task1(), Task2()])
    assert c.foo == 'task1'


def test_set_conf_value():
    class MyConf(BaseConf):
        user_value = 'user'

    c = MyConf()
    c.set_conf_value('user_value', 'my', keep_user_value=True)
    assert c.user_value == 'user'


def test_jinja2_usage():
    class MyConf(BaseConf):
        foo = 'bar'

    template = Template('{{ foo }}')
    value = template.render(**MyConf())
    assert value == u'bar'
