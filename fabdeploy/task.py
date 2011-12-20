import re
from contextlib import contextmanager

from fabric.api import env, settings
from fabric.tasks import Task as BaseTask

from .containers import MultiSourceDict
from .base import process_conf
from .utils import unprefix_conf


class Task(BaseTask):
    name = None

    def __init__(self, *args, **kwargs):
        super(Task, self).__init__(*args, **kwargs)
        if self.name is None:
            self.name = self.generate_name()
        self.conf = None

    def before_do(self):
        pass

    def after_do(self, result):
        pass

    def do(self):
        raise NotImplementedError()

    def generate_name(self):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', self.__class__.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _get_module(self):
        return self.__module__.split('.')[-1]

    def _get_namespaces(self, kwargs):
        module = self._get_module()
        ns = [
            '%s.' % module,
            '%s.' % self.name,
            '%s.%s.' % (module, self.name),
        ]
        if '_namespace' in kwargs:
            ns.append(kwargs['_namespace'])
        return ns

    def setup_conf(self, kwargs):
        if hasattr(env, 'conf'):
            conf = env.conf.copy()
            conf = unprefix_conf(conf, self._get_namespaces(kwargs))
        else:
            conf = {}

        self.conf = MultiSourceDict(
            conf, self, kwargs, name='%s.%s' % (self._get_module(), self.name))

    @contextmanager
    def tmp_conf(self, conf, **fabric_settings):
        try:
            old_kwargs = None

            if isinstance(conf, MultiSourceDict):
                self.conf = conf.copy()
            else:
                conf = process_conf(conf, use_defaults=False)
                if self.conf is None:
                    self.setup_conf(conf)
                else:
                    old_kwargs = self.conf.task_kwargs
                    self.conf.task_kwargs.update(conf)

            with settings(
                host_string=self.conf.get('address', ''), **fabric_settings):
                yield
        finally:
            if old_kwargs is not None:
                # conf can be reused, but kwargs should not
                self.conf.task_kwargs = old_kwargs
            elif self.conf:
                self.conf.task_kwargs = {}
                self.conf = None

    def run(self, **kwargs):
        with self.tmp_conf(kwargs):
            self.before_do()
            result = self.do()
            self.after_do(result)
        return result
