import os
import sys
import posixpath
import logging
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from fabric.api import env
from fabric import network

from .conf import DEFAULTS as CONF_DEFAULTS
from .containers import MultiSourceDict, AttributeDict


logger = logging.getLogger('fabdeploy')


def setup_fabdeploy():
    sys.path[0:0] = os.path.dirname(sys.path[0])

    if not hasattr(env, 'conf'):
        env.conf = MultiSourceDict(dict(
            host='%s@localhost' % os.environ['USER'],
        ))
    if not env.hosts:
        env.hosts = [env.conf.host]


def substitute(value, conf):
    if isinstance(value, list):
        for i, v in enumerate(value):
            value[i] = substitute(v, conf)
    elif isinstance(value, basestring):
        value = value % conf
    return value


def process_conf(user_conf, use_defaults=True):
    conf = MultiSourceDict(name='process_conf')

    if use_defaults:
        tmp_conf = CONF_DEFAULTS.copy()
        tmp_conf.update(user_conf)
        user_conf = tmp_conf

    if 'address' in user_conf:
        conf.setdefault('address', user_conf['address'])
        username, host, _ = network.normalize(user_conf['address'])
        conf.setdefault('user', username)
        conf.setdefault('host', host)

    for k, v in user_conf.items():
        try:
            v = substitute(v, conf)
        except ValueError:
            logger.debug('Can not format %r=%r' % (k, v))

        if k.endswith(('_dir', '_path')) and isinstance(v, (list, tuple)):
            v = posixpath.join(*v).rstrip(posixpath.sep)
        elif k.endswith(('_ldir', '_lpath')) and isinstance(v, (list, tuple)):
            v = os.path.abspath(os.path.join(*v).rstrip(os.sep))

        conf.setdefault(k, v)

    return conf


def setup_conf(user_conf):
    return MultiSourceDict(process_conf(user_conf))


def fabconf(name, base_conf=None, task_kwargs=None):
    if base_conf:
        conf = base_conf.copy()
    else:
        conf = OrderedDict()

    try:
        import fabconf as config
    except ImportError:
        pass
    else:
        name = '%s_CONF' % name.upper()
        conf.update(getattr(config, name))

    if task_kwargs:
        conf.update(task_kwargs)

    env.conf = setup_conf(conf)
    env.hosts = [env.conf.address]
