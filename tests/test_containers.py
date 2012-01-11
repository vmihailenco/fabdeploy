from jinja2 import Template

from fabdeploy.task import Task
from fabdeploy.containers import BaseConf, conf


class MyTask(Task):
    @conf
    def foo(self):
        return 'obj'


def test_set_get():
    d = BaseConf()
    d.foo = 'data'
    assert d.foo == 'data'

    d = BaseConf(task=MyTask())
    d.foo = 'data'
    assert d.foo == 'obj'

    d.setdefault('foo', 'bla')
    assert d.foo == 'obj'

    d.setdefault('bla', 'bla')
    assert d.bla == 'bla'

    assert d.get('not_exist', 'default') == 'default'


def test_jinja2_usage():
    d = BaseConf(task=MyTask())
    d.foo = 'data'

    template = Template('{{ foo }}')
    value = template.render(**d)
    assert value == u'obj'
