import os
import sys
import datetime
import posixpath
import logging
from collections import MutableMapping

from fabric import network
from fabric.api import prompt

from .utils import home_path


logger = logging.getLogger('fabdeploy')


class AttributeDict(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


class MissingVarException(Exception):
    pass


def conf(func):
    """Decorator to mark function as config source."""

    func._is_conf = True
    return func


class BaseConf(MutableMapping):
    _attrs = (
        '_name',
        '_tasks',
        '_global_conf',
        '_versions',
        '_conf_value',
        '_conf_raw_value',
        '_process_conf',
        '_substitute')

    def __init__(
        self,
        name=None,
        tasks=None,
        global_conf=None,
        versions=['active', 'last', 'previous']):
        self._name = name or 'unknown'
        self._tasks = tasks or []
        self._global_conf = global_conf or self
        self._versions = versions

        for v in ['previous', 'last', 'active']:
            self['%s_version' % v] = \
                lambda self, path_name: self._make_version(v, path_name)

        self._copy_conf(self)

    def set_name(self, name):
        self._name = name

    def add_task(self, task):
        self._tasks.append(task)

    def set_global_conf(self, conf):
        self._global_conf = conf

    def set_globally(self, name, value):
        self[name] = value
        self._global_conf[name] = value

    def _make_version(self, name, path_name):
        path = self[path_name]
        version_path = self.version_path
        new_version_path = posixpath.join(self.home_path, name)
        return path.replace(version_path, new_version_path)

    def _substitute(self, value):
        if isinstance(value, list):
            for i, v in enumerate(value):
                value[i] = self._substitute(v)
        elif isinstance(value, basestring):
            value = value % self
        return value

    def _process_conf(self, name, value):
        try:
            value = self._substitute(value)
        except ValueError:
            logger.debug(
                '_process_conf: can not substitute %r=%r' % (name, value))

        if callable(value) and hasattr(value, '_is_conf'):
            value = value()

        if name.endswith(('_dir', '_path', '_file', '_link')) and \
           isinstance(value, (list, tuple)):
            value = posixpath.join(*value).rstrip(posixpath.sep)
        elif name.endswith(('_ldir', '_lpath', '_lfile', '_llink')) and \
             isinstance(value, (list, tuple)):
            value = os.path.abspath(os.path.join(*value).rstrip(os.sep))

        return value

    def _conf_raw_value(self, name):
        for task in self._tasks:
            try:
                return task.conf_value(name)
            except MissingVarException:
                continue
        try:
            return super(BaseConf, self).__getattribute__(name)
        except AttributeError:
            raise MissingVarException

    def _conf_value(self, name, use_prompt=False):
        try:
            value = self._conf_raw_value(name)
        except MissingVarException:
            if use_prompt:
                value = prompt('%s.%s = ' % (self._name, name))
                self.set_globally(name, value)
            else:
                raise
        return self._process_conf(name, value)

    def _links(self, name, value):
        parts = name.split('_')
        if parts[-1] != 'path':
            return {}

        link_name = '_'.join(parts[:-1])
        links = {}
        for v in self._versions:
            links['%s_%s_link' % (v, link_name)] = \
                conf(lambda self, conf=self, v=v: conf._make_version(v, name))
        return links

    def set_conf_value(self, name, value, keep_user_value=False):
        if hasattr(self.__class__, name) and keep_user_value:
            return

        instancemethod = type(self.__class__.set_conf_value)
        if callable(value) and not isinstance(value, instancemethod):
            value = instancemethod(value, self, self.__class__)

        super(BaseConf, self).__setattr__(name, value)
        self._new_conf(name, value)

    def _new_conf(self, name, value):
        for link_name, link in self._links(name, value).items():
            self.set_conf_value(link_name, link, keep_user_value=True)

    def _conf_keys(self):
        builtins = set([k for k in dir(BaseConf)])
        keys = [k for k in dir(self)
                if not k.startswith('_') and k not in builtins]
        for task in self._tasks:
            keys.extend(task.conf_keys())
        return keys

    def setdefault(self, key, default=None):
        try:
            value = self._conf_raw_value(key)
        except MissingVarException:
            value = default
            self.set_conf_value(key, value)
        return value

    def get(self, key, default):
        try:
            return self._conf_value(key, use_prompt=False)
        except MissingVarException:
            return default

    def __setitem__(self, key, value):
        self.set_conf_value(key, value)

    def __getitem__(self, key):
        try:
            return self._conf_value(key)
        except MissingVarException:
            raise KeyError(key)

    def __delitem__(self, key):
        raise NotImplementedError()

    def __iter__(self):
        return iter(self._conf_keys())

    def __len__(self):
        return len(self._conf_keys())

    def __contains__(self, key):
        try:
            self._conf_value(key, use_prompt=False)
            return True
        except MissingVarException:
            return False

    def __getattribute__(self, name):
        if name in super(BaseConf, self).__getattribute__('_attrs'):
            return super(BaseConf, self).__getattribute__(name)
        try:
            return self._conf_value(name)
        except MissingVarException:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in super(BaseConf, self).__getattribute__('_attrs'):
            super(BaseConf, self).__setattr__(name, value)
            return
        self.set_conf_value(name, value)

    def _copy_conf(self, source):
        for k in source._conf_keys():
            try:
                self.set_conf_value(k, source._conf_raw_value(k))
            except MissingVarException:
                logger.debug('_copy_conf: can not copy name=%s' % k)

    def copy(self):
        d = self.__class__(
            global_conf=self._global_conf,
            tasks=self._tasks,
            name=self._name)
        d._copy_conf(self)
        return d

    def __repr__(self):
        return '%s<name=%s>' % (self.__class__.__name__, self._name)


class DefaultConf(BaseConf):
    conf_name = 'default'
    address = '%s@localhost' % os.environ['USER']
    instance_name = '%(user)s'

    time_format = '%Y.%m.%d-%H.%M.%S'

    # directory name inside src_path that contains project
    # this is useful if your project is not in git/hg repo root dir
    project_dir = ''
    # directory name that contains manage.py file (django project root)
    django_dir = ''
    home_path = conf(lambda self: home_path(self.user))
    fabdeploy_path = ['%(home_path)s', '.fabdeploy.d']
    fabdeploy_bin_path = ['%(home_path)s', '.fabdeploy.d', 'bin']
    version_path = ['%(home_path)s', '%(version)s']
    version_data_file = ['%(version_path)s', '.fabdeploy']
    src_path = ['%(version_path)s', 'src']
    project_path = ['%(src_path)s', '%(project_dir)s']
    django_path = ['%(project_path)s', '%(django_dir)s']
    env_path = ['%(version_path)s', 'env']
    shared_path = ['%(home_path)s', 'shared']
    media_path = ['%(shared_path)s', 'media']
    etc_path = ['%(shared_path)s', 'etc']
    var_path = ['%(shared_path)s', 'var']
    log_path = ['%(var_path)s', 'log']
    backup_path = ['%(var_path)s', 'backup']

    project_ldir = ''
    django_ldir = '%(django_dir)s'
    home_lpath = sys.path[0]
    src_lpath = '%(home_lpath)s'
    project_lpath = ['%(src_lpath)s', '%(project_ldir)s']
    django_lpath = ['%(src_lpath)s', '%(django_ldir)s']

    # user that have sudo right
    # this is useful, because usually deploy user don't have sudo right
    sudo_user = 'root'
    server_name = '%(host)s'
    server_admin = 'admin@%(host)s'

    apache_processes = 1
    # conf decorator is used to achieve lazy evaluation
    apache_threads = conf(lambda self: self.cpu_count * 2 + 1)
    uwsgi_processes = conf(lambda self: self.cpu_count * 2 + 1)

    config_templates_lpathes = [
        'config_templates/%(conf_name)s',
        'config_templates',
    ]

    # django settings: manage.py --settings=%(settings)s
    settings = 'settings'
    # env specific settings file, that is imported in %(settings)s
    local_settings_file = 'local_settings.py'
    # %(local_settings_file)s will be replaced with this file
    remote_settings_lfile = 'prod_settings.py'
    loglevel = 'INFO'

    db_name = '%(instance_name)s'
    db_user = '%(user)s'
    db_password = '%(user)s'
    db_host = 'localhost'
    mysql__db_root_user = 'root'
    mysql__db_root_password = 'mysql'
    mysql__db_port = 3306
    postgres__db_root_user = 'postgres'
    postgres__db_root_password = 'postgres'
    postgres__db_port = 5432

    pip_cache_path = '/var/run/pip-download-cache'
    pip_req_lpath = ''
    pip_req_file = 'requirements.txt'

    # prefix for supervisor programs/groups
    # useful when there are several projects deployed on one server
    supervisor_prefix = ''
    supervisor_config_path = ['%(etc_path)s', 'supervisor']
    supervisord_config_file = '/etc/supervisord.conf'

    @conf
    def user(self):
        username, _, _ = network.normalize(self.address)
        return username

    @conf
    def host(self):
        _, host, _ = network.normalize(self.address)
        return host

    @conf
    def current_time(self):
        return datetime.datetime.utcnow().strftime(self.time_format)

    @conf
    def version(self):
        self.set_globally('version', self.current_time)
        return self.version

    @conf
    def os(self):
        from fabdeploy import system
        with system.os_codename.tmp_conf():
            self.set_globally('os', system.os_codename.os_codename())
        return self.os

    @conf
    def cpu_count(self):
        from fabdeploy import system
        with system.cpu_count.tmp_conf():
            self.set_globally('cpu_count', system.cpu_count.cpu_count())
        return self.cpu_count

    def config_template_lpath(self, name):
        for dir in self.config_templates_lpathes:
            path = os.path.join(dir, name)
            if os.path.exists(path):
                return path
