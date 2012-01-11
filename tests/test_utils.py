from fabdeploy.utils import unprefix_conf


def test_unprefix_conf():
    conf = {'module__foo': 'module', 'foo': 'bar'}
    unprefix_conf(conf, ['module__'])
    assert conf['foo'] == 'module'
