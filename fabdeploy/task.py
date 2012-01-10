import re
import inspect
from contextlib import contextmanager

from fabric.api import env, settings
from fabric.tasks import Task as BaseTask

from .containers import BaseConf, MissingVarException
from .utils import unprefix_conf


class Task(BaseTask):
    name = None
    _curr_conf_names = set()

    def __init__(self, *args, **kwargs):
        super(Task, self).__init__(*args, **kwargs)
        if self.name is None:
            self.name = self._generate_name()
        self.conf = None

    def before_do(self):
        pass

    def after_do(self, result):
        pass

    def do(self):
        raise NotImplementedError()

    def conf_keys(self):
        keys = set()
        keys.update(self.task_kwargs.keys())
        for name, value in inspect.getmembers(self):
            if hasattr(value, '_is_conf'):
                keys.add(name)
        return keys

    def conf_value(self, name, null=object()):
        if name in self._curr_conf_names:
            raise MissingVarException
        self._curr_conf_names.add(name)
        value = null

        if name in self.task_kwargs:
            value = self.task_kwargs[name]
        else:
            try:
                attr = getattr(self, name)
                if hasattr(attr, '_is_conf'):
                    value = attr()
            except AttributeError:
                pass

        self._curr_conf_names.remove(name)
        if value is not null:
            return value
        else:
            raise MissingVarException

    def _generate_name(self):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', self.__class__.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _get_module(self):
        return self.__module__.split('.')[-1]

    def _namespaces(self, kwargs):
        module = self._get_module()
        ns = [
            '%s__' % module,
            '%s__' % self.name,
            '%s__%s__' % (module, self.name),
        ]
        if '_namespace' in kwargs:
            ns.append(kwargs['_namespace'])
        return ns

    @contextmanager
    def tmp_conf(self, conf=None, task_kwargs=None, **fabric_settings):
        try:
            self.task_kwargs = task_kwargs or {}

            if conf is None:
                self.conf = env.conf.copy()
                self.conf.set_global_conf(env.conf)
                self.conf.set_task(self)
            else:
                assert isinstance(conf, BaseConf)
                self.conf = conf.copy()
            self.conf.set_name('%s.%s' % (self._get_module(), self.name))
            unprefix_conf(self.conf, self._namespaces(self.task_kwargs))

            with settings(
                host_string=self.conf.get('address', ''), **fabric_settings):
                yield
        finally:
            self.task_kwargs = None
            self.conf = None

    def run(self, **kwargs):
        with self.tmp_conf(task_kwargs=kwargs):
            self.before_do()
            result = self.do()
            self.after_do(result)
        return result
