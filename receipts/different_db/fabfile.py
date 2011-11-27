import os
import sys

DIRNAME = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(os.path.dirname(DIRNAME)))

from fabdeploy import monkey; monkey.patch_all()
from fabric.api import *
import fabdeploy
from fabdeploy.api import *; setup_fabdeploy()


@task
def dev():
    fabconf('dev')
    env.conf.db = getattr(fabdeploy, env.conf.db)


@task
def prod():
    fabconf('prod')
    env.conf.db = getattr(fabdeploy, env.conf.db)


@task
def execute():
    print env.conf.db.execute
