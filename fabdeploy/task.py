import re
import datetime
from contextlib import contextmanager

from fabric.api import env, settings
from fabric.tasks import Task as BaseTask
from fabric.network import disconnect_all

from fabdeploy.base import setup_conf
from fabdeploy.containers import MultiSourceDict, conf
from fabdeploy.utils import unprefix_conf


class Task(BaseTask):
    def __init__(self):
        if self.name == 'undefined':
            self.name = self.generate_name()

    def before_do(self):
        pass

    def after_do(self, result):
        pass

    def do(self):
        raise NotImplementedError()

    @conf
    def current_time(self):
        return datetime.datetime.utcnow().strftime(self.conf.time_format)

    def generate_name(self):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', self.__class__.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def get_prefixes(self):
        module = self.__module__.split('.')[-1]
        return [
            '%s.' % module,
            '%s.' % self.name,
            '%s.%s.' % (module, self.name),
        ]

    def setup_conf(self, kwargs):
        if hasattr(env, 'conf'):
            conf = env.conf.copy()
            conf = unprefix_conf(conf, self.get_prefixes())
        else:
            conf = {}
        conf.update(kwargs)
        self.conf = MultiSourceDict(conf, self)

    @contextmanager
    def custom_conf(self, conf):
        try:
            old_conf = env.get('conf')
            env.conf = setup_conf(conf)

            # TODO: add abort_on_prompts=True
            with settings(host_string=env.conf.host):
                yield
        finally:
            disconnect_all()
            env.conf = old_conf

    def run(self, **kwargs):
        method = kwargs.pop('_method', 'do')
        self.setup_conf(kwargs)

        self.before_do()
        result = getattr(self, method)()
        self.after_do(result)
        return result
