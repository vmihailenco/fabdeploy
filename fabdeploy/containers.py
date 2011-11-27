import inspect
from collections import MutableMapping
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from fabric.api import prompt


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
        'name',
        'conf',
        'permanent_conf',
        'task',
        'task_conf_keys',
        'task_kwargs')

    def __init__(
        self,
        conf=None,
        task=None,
        task_kwargs=None,
        permanent_conf=None,
        name=None):
        self.name = name or ''
        self.conf = conf or {}
        self.permanent_conf = permanent_conf or self

        self.task = task
        self.task_conf_keys = set()
        for name, value in inspect.getmembers(self.task):
            if hasattr(value, '_is_conf'):
                self.task_conf_keys.add(name)

        self.task_kwargs = task_kwargs or {}

    def process_conf(self, conf, name):
        value = conf[name]
        if callable(value) and hasattr(value, '_is_conf'):
            value = value(self)
            if name in self.task_kwargs:
                self.permanent_conf[name] = self.task_kwargs[name]
        return value

    def get_value(self, name, use_prompt=True):
        if name in self.task_kwargs:
            return self.process_conf(self.task_kwargs, name)

        if name in self.task_conf_keys:
            # delete to avoid recursion
            self.task_conf_keys.remove(name)
            r = getattr(self.task, name)()
            self.task_conf_keys.add(name)
            return r

        if name not in self.conf:
            if isinstance(name, basestring) and not name.startswith('_') and \
                    use_prompt:
                self.conf[name] = prompt('%s.%s = ' % (self.name, name))
                self.permanent_conf[name] = self.conf[name]
            else:
                raise MissingVarException(name)

        return self.process_conf(self.conf, name)

    def set_value(self, name, value):
        self.task_kwargs[name] = value

    def get_keys(self):
        keys = self.task_conf_keys.copy()
        keys.update(self.conf.keys())
        keys.update(self.task_kwargs.keys())
        return keys

    def setdefault(self, key, default=None):
        try:
            value = self.get_value(key, use_prompt=False)
        except MissingVarException:
            value = default
            self.set_value(key, value)
        return value

    def get(self, key, default):
        try:
            return self.get_value(key, use_prompt=False)
        except MissingVarException:
            return default

    def __setitem__(self, key, value):
        self.set_value(key, value)

    def __getitem__(self, key):
        try:
            return self.get_value(key)
        except MissingVarException:
            raise KeyError(key)

    def __delitem__(self, key):
        raise NotImplementedError()

    def __iter__(self):
        return iter(self.get_keys())

    def __len__(self):
        return len(self.get_keys())

    def __contains__(self, key):
        try:
            self.get_value(key, use_prompt=False)
            return True
        except MissingVarException:
            return False

    def __getattr__(self, name):
        try:
            return self.get_value(name)
        except MissingVarException:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in self._attrs:
            self.__dict__[name] = value
        else:
            self.set_value(name, value)

    def copy(self):
        return MultiSourceDict(
            conf=self.con,
            task=self.task,
            task_kwargs=self.task_kwargs,
            permanent_conf=self.permanent_conf,
            name=self.name)

    def __repr__(self):
        return repr(dict(self))


def conf(func):
    """Decorator to mark function as config source."""

    func._is_conf = True
    return func
