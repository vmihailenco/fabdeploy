from jinja2 import Template

from fabdeploy.containers import MultiSourceDict, conf


class DataSource(object):
    @conf
    def foo(self):
        return 'obj'


def test_set_get():
    data = {'foo': 'data'}
    obj = DataSource()

    d = MultiSourceDict(data)
    assert d.foo == 'data'

    d = MultiSourceDict(data, obj)
    assert d.foo == 'obj'

    d.setdefault('foo', 'bla')
    assert d.foo == 'obj'

    d.setdefault('bla', 'bla')
    assert d.bla == 'bla'

    assert d.get('not_exist', 'default') == 'default'


def test_jinja2_usage():
    data = {'foo': 'data'}
    obj = DataSource()

    d = MultiSourceDict(data, obj)

    template = Template('{{ foo }}')
    value = template.render(**d)
    assert value == u'obj'
