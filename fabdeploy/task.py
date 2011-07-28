import re
import datetime

from fabric.api import env
from fabric.tasks import Task as BaseTask

from fabdeploy.containers import MultiSourceDict, conf
from fabdeploy.utils import unprefix_conf


class Task(BaseTask):
    def __init__(self, conf=None):
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
        conf = env.conf.copy()
        conf = unprefix_conf(conf, self.get_prefixes())
        conf.update(kwargs)
        self.conf = MultiSourceDict(conf, self)

    def run(self, **kwargs):
        self.setup_conf(kwargs)

        self.before_do()
        result = self.do()
        self.after_do(result)
        return result
