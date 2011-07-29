import os
import posixpath
import logging
from collections import OrderedDict

from fabric.api import env
from fabric import network
from fabric.state import _AttributeDict

from fabdeploy.containers import MultiSourceDict
from fabdeploy.utils import get_home_dir


logger = logging.getLogger('fabdeploy')


def setup_fabdeploy():
    if not hasattr(env, 'conf'):
        env.conf = MultiSourceDict()
    if not env.hosts:
        env.hosts = ['%s@localhost' % os.environ['USER']]


def get_config_template_path(name):
    for dir in env.conf.config_templates_pathes:
        path = os.path.join(dir, name)
        if os.path.exists(path):
            return path


def get_pip_req_path(name):
    return posixpath.join(env.conf.pip_req_path, name)


def get_django_lpath(name):
    return os.path.join(env.conf.django_path, name)


def get_django_path(name):
    return posixpath.join(env.conf.django_dir, name)


DEFAULTS = OrderedDict([
    ('instance_name', '%(user)s'),
    ('project_path', ''),
    ('django_path', ''),
    ('django_path_getter', get_django_path),
    ('django_lpath_getter', get_django_lpath),

    ('home_dir', lambda conf: get_home_dir(conf.user)),
    ('src_dir', ['%(home_dir)s', 'src', '%(instance_name)s']),
    ('project_dir', ['%(src_dir)s', '%(project_path)s']),
    ('django_dir', ['%(project_dir)s', '%(django_path)s']),
    ('env_dir', ['%(home_dir)s', 'envs', '%(instance_name)s']),
    ('etc_dir', ['%(env_dir)s', 'etc']),
    ('var_dir', ['%(env_dir)s', 'var']),
    ('log_dir', ['%(var_dir)s', 'log']),
    ('backups_dir', ['%(var_dir)s', 'backups']),

    ('time_format', '%Y.%m.%d-%H.%M'),
    ('sudo_user', 'root'),
    ('server_name', '%(host)s'),
    ('server_admin', 'admin@%(host)s'),

    ('apache_processes', 1),
    ('apache_threads', 15),
    ('uwsgi_processes', 5),

    ('config_templates_lpath_getter', get_config_template_path),
    ('config_templates_pathes', ['config_templates']),

    ('settings', 'settings'),
    ('local_settings_file', 'local_settings.py'),
    ('remote_settings_file', 'prod_settings.py'),
    ('loglevel', 'INFO'),

    ('db_name', '%(instance_name)s'),
    ('db_user', '%(user)s'),
    ('db_password', '%(user)s'),
    ('db_host', 'localhost'),
    ('mysql.db_root_user', 'postgres'),
    ('mysql.db_port', 3306),
    ('postgres.db_root_user', 'postgres'),
    ('postgres.db_port', 5432),

    ('pip_cache_dir', ['%(var_dir)s', 'pip']),
    ('pip_req_path_getter', get_pip_req_path),
    ('pip_req_path', 'reqs'),
    ('pip_req_name', 'active.txt'),

    ('supervisor_prefix', ''),
    ('supervisor_config_dir', ['%(etc_dir)s', 'supervisor']),
    ('supervisord_config', '/etc/supervisord.conf'),
])


def substitute(value, conf):
    if isinstance(value, list):
        for i, v in enumerate(value):
            value[i] = substitute(v, conf)
    elif isinstance(value, basestring):
        value = value % conf
    return value


def setup_conf(user_conf):
    conf = _AttributeDict()

    conf.setdefault('address', user_conf['address'])
    user, host, port = network.normalize(conf.address)
    conf.setdefault('user', user)
    conf.setdefault('host', host)

    merged_conf = DEFAULTS.copy()
    merged_conf.update(user_conf)
    for k, v in merged_conf.items():
        if callable(v) and not k.endswith('_getter'):
            v = v(conf)

        try:
            v = substitute(v, conf)
        except ValueError:
            logger.debug('Can not format %r=%r' % (k, v))
            pass

        if k.endswith(('_dir', '_path')) and isinstance(v, (list, tuple)):
            v = posixpath.join(*v).rstrip(posixpath.sep)
        elif k.endswith(('_ldir', '_lpath')) and isinstance(v, (list, tuple)):
            v = os.path.abspath(os.path.join(*v).rstrip(os.sep))

        conf.setdefault(k, v)

    return conf
