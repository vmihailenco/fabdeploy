import re
import datetime
from contextlib import contextmanager

from fabric.api import env, settings
from fabric.tasks import Task as BaseTask

from fabdeploy.containers import MultiSourceDict, conf
from fabdeploy.base import process_conf
from fabdeploy.utils import unprefix_conf


class Task(BaseTask):
    def __init__(self, *args, **kwargs):
        super(Task, self).__init__(*args, **kwargs)
        if self.name == 'undefined':
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

    def get_prefixes(self):
        module = self._get_module()
        return [
            '%s.' % module,
            '%s.' % self.name,
            '%s.%s.' % (module, self.name),
        ]

    def setup_conf(self, kwargs):
        if getattr(env, 'conf', None):
            conf = env.conf.copy()
            conf = unprefix_conf(conf, self.get_prefixes())
        else:
            conf = {}

        self.conf = MultiSourceDict(conf, self, kwargs,
            name='%s.%s' % (self._get_module(), self.name))

    @contextmanager
    def tmp_conf(self, conf, **fabric_settings):
        try:
            old_kwargs = None

            if isinstance(conf, MultiSourceDict):
                self.conf = conf
            else:
                conf = process_conf(conf, use_defaults=False)
                if self.conf is None:
                    self.setup_conf(conf)
                else:
                    old_kwargs = self.conf.kwargs
                    self.conf.kwargs.update(conf)

            with settings(host_string=env.conf.get('address', ''),
                          **fabric_settings):
                yield
        finally:
            if old_kwargs is not None:
                # conf can be reused, but kwargs should not
                self.conf.kwargs = old_kwargs
            elif self.conf:
                self.conf.kwargs = {}
                self.conf = None

    def run(self, **kwargs):
        with self.tmp_conf(kwargs):
            self.before_do()
            result = self.do()
            self.after_do(result)
        return result
