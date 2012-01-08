import os
import sys
import posixpath
import logging
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from fabric.api import env, abort
from fabric import network

from .conf import DEFAULTS as CONF_DEFAULTS
from .containers import MultiSourceDict


logger = logging.getLogger('fabdeploy')


def setup_fabdeploy():
    sys.path[0:0] = os.path.dirname(sys.path[0])

    if not hasattr(env, 'conf'):
        env.conf = MultiSourceDict(name='setup_fabdeploy')
        env.conf.provide_conf('address', '%s@localhost' % os.environ['USER'])

    if not env.hosts:
        env.hosts = [env.conf.host]


def setup_conf(user_conf):
    c = MultiSourceDict(name='global')
    for k, v in CONF_DEFAULTS.items():
        c.provide_conf(k, v)
    for k, v in user_conf.items():
        c.provide_conf(k, v)
    return c
