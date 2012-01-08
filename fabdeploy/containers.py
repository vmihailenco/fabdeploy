import os
import posixpath
import logging
from collections import MutableMapping
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
from functools import partial

from fabric import network
from fabric.api import prompt


logger = logging.getLogger('fabdeploy')


class AttributeDict(OrderedDict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


class MissingVarException(Exception):
    pass


class MultiSourceDict(MutableMapping):
    """
    Dict that looks for the key in several places.
    """

    _attrs = (
        '_name',
        '_conf',
        '_global_conf',
        '_task',
        '_user_conf')

    def __init__(
        self,
        task=None,
        global_conf=None,
        name=None):
        self._name = name or 'unknown'
        self._conf = OrderedDict()
        self._task = task
        self._global_conf = global_conf or self
        self._user_conf = {}

    def set_name(self, name):
        self._name = name

    def set_task(self, task):
        self._task = task

    def set_global_conf(self, conf):
        self._global_conf = conf

    def set_globally(self, name, value):
        self.provide_conf(name, value)
        self._global_conf.provide_conf(name, value)

    def provide_conf(self, name, value):
        self._conf[name] = value
        self._new_conf(name, value, self._conf)

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

        if callable(value):
            if hasattr(value, '_is_conf'):
                value = value(conf=self._global_conf)
            else:
                value = partial(value, conf=self._global_conf)

        if name.endswith(('_dir', '_path', '_file', '_link')) and \
           isinstance(value, (list, tuple)):
            value = posixpath.join(*value).rstrip(posixpath.sep)
        elif name.endswith(('_ldir', '_lpath')) and \
             isinstance(value, (list, tuple)):
            value = os.path.abspath(os.path.join(*value).rstrip(os.sep))

        return value

    def _conf_raw_value(self, name):
        try:
            return self._user_conf[name]
        except KeyError:
            pass

        if self._task and name not in self._task.curr_conf_names:
            try:
                return self._task.conf_value(name)
            except MissingVarException:
                pass

        if name in self._conf:
            return self._conf[name]

        raise MissingVarException

    def _raw_value(self, name, use_prompt=False):
        try:
            value = self._conf_raw_value(name)
        except MissingVarException:
            if use_prompt:
                value = prompt('%s.%s = ' % (self._name, name))
                self.set_globally(name, self._conf[name])
            else:
                raise
        return self._process_conf(name, value)

    def _links(self, name, value):
        parts = name.split('_')
        if parts[-1] != 'path':
            return {}
        link_name = '_'.join(parts[:-1])

        make_version = self._conf_raw_value('make_version')
        versions = self._conf_raw_value('versions')

        links = {}
        for v in versions:
            links['%s_%s_link' % (v, link_name)] = \
                conf(lambda conf, v=v: make_version(v, name, conf=conf))
        return links

    def _set_value(self, name, value):
        self._user_conf[name] = value
        self._new_conf(name, value, self._user_conf)

    def _new_conf(self, name, value, storage):
        if name == 'address':
            username, host, _ = network.normalize(value)
            storage['user'] = username
            storage['host'] = host

        for link_name, link in self._links(name, value).items():
            storage.setdefault(link_name, link)

        if '.' in name:
            storage.setdefault(name.replace('.', '__'), value)

    def _conf_keys(self):
        keys = set()
        keys.update(self._conf.keys())
        keys.update(self._user_conf.keys())
        if self._task:
            keys.update(self._task.conf_keys())
        return keys

    def setdefault(self, key, default=None):
        try:
            value = self._raw_value(key, use_prompt=False)
        except MissingVarException:
            value = default
            self._set_value(key, value)
        return value

    def get(self, key, default):
        try:
            return self._raw_value(key, use_prompt=False)
        except MissingVarException:
            return default

    def __setitem__(self, key, value):
        self._set_value(key, value)

    def __getitem__(self, key):
        try:
            return self._raw_value(key)
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
            self._raw_value(key, use_prompt=False)
            return True
        except MissingVarException:
            return False

    def __getattr__(self, name):
        try:
            return self._raw_value(name)
        except MissingVarException:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in self._attrs:
            self.__dict__[name] = value
        else:
            self._set_value(name, value)

    def copy(self):
        d = MultiSourceDict(
            task=self._task,
            global_conf=self._global_conf,
            name=self._name)
        d._conf = self._conf.copy()
        return d

    def __repr__(self):
        return repr(dict(self))


def conf(func):
    """Decorator to mark function as config source."""

    func._is_conf = True
    return func
