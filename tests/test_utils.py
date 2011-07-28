from fabdeploy.utils import unprefix_conf


def test_unprefix_conf():
    conf = {'module.foo': 'module', 'foo': 'bar'}
    conf = unprefix_conf(conf, ['module.'])
    assert conf['foo'] == 'module'
