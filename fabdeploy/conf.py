import os
import sys
import posixpath
import datetime
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from .containers import conf
from .utils import home_path


def config_template_path(name, conf=None):
    for dir in conf.config_templates_pathes:
        path = os.path.join(dir, name)
        if os.path.exists(path):
            return path


# TODO: this should be renamed since in returns relative path for jinja2
def django_lpath(name, conf=None):
    return os.path.join(conf.django_ldir, name)


def django_path(name, conf=None):
    return posixpath.join(conf.django_path, name)


def pip_req_path(name, conf=None):
    return posixpath.join(conf.pip_req_path, name)


@conf
def os_codename(conf):
    from fabdeploy import system
    conf.set_globally('os', system.os_codename.codename())
    return conf.os


@conf
def cpu_count(conf):
    from fabdeploy import system
    conf.set_globally('cpu_count', system.cpu_count.cpu_count())
    return conf.cpu_count


@conf
def current_time(conf):
    return datetime.datetime.utcnow().strftime(conf.time_format)


@conf
def version(conf):
    conf.set_globally('version', conf.current_time)
    return conf.version


def make_version(name, path_name, conf=None):
    path = getattr(conf, path_name)
    version_path = conf.version_path
    new_version_path = posixpath.join(conf.home_path, name)
    return path.replace(version_path, new_version_path)


DEFAULTS = OrderedDict([
    ('conf_name', 'default'),
    ('address', '%s@localhost' % os.environ['USER']),

    ('os', os_codename),
    ('cpu_count', cpu_count),
    ('time_format', '%Y.%m.%d-%H.%M.%S'),
    ('current_time', current_time),

    ('instance_name', '%(user)s'),

    ('version', version),
    ('versions', ['active', 'last', 'previous']),
    ('make_version', make_version),

    ('django_path_getter', django_path),
    ('django_lpath_getter', django_lpath),

    # directory name inside src_path that contains project
    # this is useful if your project is not in git/hg repo root dir
    ('project_dir', ''),
    # directory name that contains manage.py file (django project root)
    ('django_dir', ''),
    ('home_path', conf(lambda conf: home_path(conf.user))),
    ('version_path', ['%(home_path)s', '%(version)s']),
    ('src_path', ['%(version_path)s', 'src']),
    ('project_path', ['%(src_path)s', '%(project_dir)s']),
    ('django_path', ['%(project_path)s', '%(django_dir)s']),
    ('env_path', ['%(version_path)s', 'env']),
    ('etc_path', ['%(env_path)s', 'etc']),
    ('var_path', ['%(env_path)s', 'var']),
    ('log_path', ['%(var_path)s', 'log']),
    ('backup_path', ['%(var_path)s', 'backup']),

    ('project_ldir', ''),
    ('django_ldir', '%(django_dir)s'),
    ('home_lpath', sys.path[0]),
    ('src_lpath', '%(home_lpath)s'),
    ('project_lpath', ['%(src_lpath)s', '%(project_ldir)s']),
    ('django_lpath', ['%(src_lpath)s', '%(django_ldir)s']),

    ('version_data_file', ['%(version_path)s', '.fabdeploy']),

    # user that have sudo right
    # this is useful, because usually deploy user don't have sudo right
    ('sudo_user', 'root'),
    ('server_name', '%(host)s'),
    ('server_admin', 'admin@%(host)s'),

    ('apache_processes', 1),
    # conf decorator is used to achieve lazy evaluation
    ('apache_threads', conf(lambda conf: conf.cpu_count * 2 + 1)),
    ('uwsgi_processes', conf(lambda conf: conf.cpu_count * 2 + 1)),

    ('config_templates_lpath_getter', config_template_path),
    ('config_templates_pathes', [
        'config_templates/%(conf_name)s',
        'config_templates',
    ]),

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

    ('pip_cache_path', '/var/run/pip-download-cache'),
    ('pip_req_path_getter', pip_req_path),
    ('pip_req_path', 'reqs'),
    ('pip_req_name', 'active.txt'),

    # prefix for supervisor programs/groups
    # useful when there several projects deployed on one server
    ('supervisor_prefix', ''),
    ('supervisor_config_path', ['%(etc_path)s', 'supervisor']),
    ('supervisord_config', '/etc/supervisord.conf'),
])

for v in ['previous', 'last', 'active']:
    DEFAULTS.update({
        '%s_version' % v:
            lambda path_name, conf=None: make_version(v, path_name, conf=conf),
    })
