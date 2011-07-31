import copy

from fabric.api import prompt

import inspect
from collections import MutableMapping


class MissingVarException(Exception):
    pass


class MultiSourceDict(MutableMapping):
    def __init__(self, data=None, obj=None):
        if data:
            self.data = data
        else:
            self.data = {}

        self.obj = obj
        self.obj_conf_keys = set()
        for name, value in inspect.getmembers(self.obj):
            if hasattr(value, '_is_conf'):
                self.obj_conf_keys.add(name)

    def get_value(self, name, use_prompt=True):
        if name in self.obj_conf_keys:
            # delete to avoid recursion
            self.obj_conf_keys.remove(name)
            r = getattr(self.obj, name)()
            self.obj_conf_keys.add(name)
            return r
        if name not in self.data:
            if not name.startswith('_') and use_prompt:
                self.data[name] = prompt('%s = ' % name)
            else:
                raise MissingVarException(name)

        return self.data[name]

    def set_value(self, name, value):
        self.data[name] = value

    def get_keys(self):
        keys = self.obj_conf_keys.copy()
        keys.update(self.data.keys())
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
            self.get_value(key)
            return True
        except MissingVarException:
            return False

    def __getattr__(self, name):
        try:
            return self.get_value(name)
        except MissingVarException:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in ['data', 'obj', 'obj_conf_keys']:
            self.__dict__[name] = value
        else:
            self.set_value(name, value)

    def copy(self):
        return copy.deepcopy(self)


def conf(func):
    func._is_conf = True
    return func
