from fabric.api import env

from fabdeploy.base import fabconf


def test_fabconf():
    fabconf('test')

    assert env.conf.foo == 'bar'
