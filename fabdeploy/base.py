import os
import sys
import logging

from fabric.api import env

from .containers import DefaultConf


logger = logging.getLogger('fabdeploy')


def setup_fabdeploy():
    sys.path[0:0] = os.path.dirname(sys.path[0])

    if not hasattr(env, 'conf'):
        env.conf = DefaultConf(name='setup_fabdeploy')

    if not env.hosts:
        env.hosts = [env.conf.host]
