import os
import sys
import posixpath
import logging
import datetime
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from fabric.api import env
from fabric import network

from fabdeploy.containers import MultiSourceDict, AttributeDict, conf
from fabdeploy.utils import get_home_path


logger = logging.getLogger('fabdeploy')


def setup_fabdeploy():
    sys.path[0:0] = os.path.dirname(sys.path[0])

    if not hasattr(env, 'conf'):
        env.conf = MultiSourceDict(dict(
            host='%s@localhost' % os.environ['USER'],
        ))
    if not env.hosts:
        env.hosts = [env.conf.host]


def get_config_template_path(name):
    for dir in env.conf.config_templates_pathes:
        path = os.path.join(dir, name)
        if os.path.exists(path):
            return path


def get_pip_req_path(name):
    return posixpath.join(env.conf.pip_req_path, name)


# TODO: this should be renamed since in returns relative path for jinja2
def get_django_lpath(name):
    return os.path.join(env.conf.django_ldir, name)


def get_django_path(name):
    return posixpath.join(env.conf.django_path, name)


@conf
def os_codename(conf):
    from fabdeploy import system
    conf.os = system.os_codename.run()
    return conf.os


@conf
def cpu_count(conf):
    from fabdeploy import system
    conf.cpu_count = system.cpu_count.run()
    return conf.cpu_count


@conf
def current_time(conf):
    return datetime.datetime.utcnow().strftime(conf.time_format)


DEFAULTS = OrderedDict([
    ('os', os_codename),
    ('cpu_count', cpu_count),

    ('instance_name', '%(user)s'),
    ('django_path_getter', get_django_path),
    ('django_lpath_getter', get_django_lpath),

    # directory name inside src_path that contains project
    # this is useful if your project is not in git/hg repo root dir
    ('project_dir', ''),
    # directory name that contains manage.py file (django project root)
    ('django_dir', ''),
    ('home_path', conf(lambda conf: get_home_path(conf.user))),
    ('src_path', ['%(home_path)s', 'src', '%(instance_name)s']),
    ('project_path', ['%(src_path)s', '%(project_dir)s']),
    ('django_path', ['%(project_path)s', '%(django_dir)s']),
    ('env_path', ['%(home_path)s', 'envs', '%(instance_name)s']),
    ('etc_path', ['%(env_path)s', 'etc']),
    ('var_path', ['%(env_path)s', 'var']),
    ('log_path', ['%(var_path)s', 'log']),
    ('backups_path', ['%(var_path)s', 'backups']),

    ('project_ldir', ''),
    ('django_ldir', '%(django_dir)s'),
    ('home_lpath', sys.path[0]),
    ('src_lpath', '%(home_lpath)s'),
    ('project_lpath', ['%(src_lpath)s', '%(project_ldir)s']),
    ('django_lpath', ['%(src_lpath)s', '%(django_ldir)s']),

    ('time_format', '%Y.%m.%d-%H.%M'),
    ('current_time', current_time),
    # user that have sudo right
    # this is useful, because usually deploy user don't have sudo right
    ('sudo_user', 'root'),
    ('server_name', '%(host)s'),
    ('server_admin', 'admin@%(host)s'),

    ('apache_processes', 1),
    ('apache_threads', conf(lambda conf: conf.cpu_count * 2 + 1)),
    ('uwsgi_processes', conf(lambda conf: conf.cpu_count * 2 + 1)),

    ('config_templates_lpath_getter', get_config_template_path),
    ('config_templates_pathes', ['config_templates']),

    # django settings: manage.py --settings=%(settings)s
    ('settings', 'settings'),
    # env specific settings file, that is imported in %(settings)s
    ('local_settings_file', 'local_settings.py'),
    # %(local_settings_file)s will be replaced with this file
    ('remote_settings_file', 'prod_settings.py'),
    ('loglevel', 'INFO'),

    ('db_name', '%(instance_name)s'),
    ('db_user', '%(user)s'),
    ('db_password', '%(user)s'),
    ('db_host', 'localhost'),
    ('mysql.db_root_user', 'root'),
    ('mysql.db_port', 3306),
    ('postgres.db_root_user', 'postgres'),
    ('postgres.db_port', 5432),

    ('pip_cache_path', ['%(var_path)s', 'pip']),
    ('pip_req_path_getter', get_pip_req_path),
    ('pip_req_path', 'reqs'),
    ('pip_req_name', 'active.txt'),

    # prefix for supervisor programs/groups
    # useful when there several projects deployed on one server
    ('supervisor_prefix', ''),
    ('supervisor_config_path', ['%(etc_path)s', 'supervisor']),
    ('supervisord_config', '/etc/supervisord.conf'),
])


def substitute(value, conf):
    if isinstance(value, list):
        for i, v in enumerate(value):
            value[i] = substitute(v, conf)
    elif isinstance(value, basestring):
        value = value % conf
    return value


def process_conf(user_conf, use_defaults=True):
    user_conf = AttributeDict(user_conf or {})
    conf = MultiSourceDict(name='process_conf')

    if 'address' in user_conf:
        conf.setdefault('address', user_conf.address)
        username, host, _ = network.normalize(conf.address)
        conf.setdefault('user', username)
        conf.setdefault('host', host)

    if use_defaults:
        merged_conf = DEFAULTS.copy()
        merged_conf.update(user_conf)
    else:
        merged_conf = user_conf

    for k, v in merged_conf.items():
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


def fabconf(name, base_conf, kwargs=None):
    conf = base_conf.copy()

    try:
        import fabconf as config
    except ImportError:
        pass
    else:
        name = '%s_CONF' % name.upper()
        conf.update(getattr(config, name))

    if kwargs:
        conf.update(kwargs)

    env.conf = setup_conf(conf)
    env.hosts = [env.conf.address]
