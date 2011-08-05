import os
import sys
import posixpath
import logging
from collections import OrderedDict

from fabric.api import env
from fabric import network

from fabdeploy.containers import MultiSourceDict
from fabdeploy.utils import get_home_path, user, detect_os


logger = logging.getLogger('fabdeploy')


def patch_sudo():
    from fabric import operations
    from fabric.operations import _run_command

    def _patched_run_command(*args, **kwargs):
        sudo = kwargs.get('sudo', False)
        if sudo:
            with user(env.conf.sudo_user):
                return _run_command(*args, **kwargs)
        else:
            return _run_command(*args, **kwargs)

    operations._run_command = _patched_run_command


def setup_fabdeploy(patch=True):
    if patch:
        patch_sudo()

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


# TODO: this should be renamed since in returns relative path for jinja2
def get_django_lpath(name):
    return os.path.join(env.conf.django_ldir, name)


def get_django_path(name):
    return posixpath.join(env.conf.django_path, name)


DEFAULTS = OrderedDict([
    ('instance_name', '%(user)s'),
    ('django_path_getter', get_django_path),
    ('django_lpath_getter', get_django_lpath),

    ('project_dir', ''),
    ('django_dir', ''),
    ('home_path', lambda conf: get_home_path(conf.user)),
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

    ('pip_cache_path', ['%(var_path)s', 'pip']),
    ('pip_req_path_getter', get_pip_req_path),
    ('pip_req_path', 'reqs'),
    ('pip_req_name', 'active.txt'),

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


def setup_conf(user_conf):
    conf = MultiSourceDict()

    conf.setdefault('address', user_conf['address'])
    username, host, _ = network.normalize(conf.address)
    conf.setdefault('user', username)
    conf.setdefault('host', host)

    if 'os' not in user_conf:
        conf.setdefault('os', detect_os(conf.address))

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
