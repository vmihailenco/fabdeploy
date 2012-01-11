import os
import sys

DIRNAME = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(os.path.dirname(DIRNAME)))

from fabdeploy import monkey; monkey.patch_all()
from fabric.api import *
from fabdeploy.api import *; setup_fabdeploy()


@task
def execute():
    print env.conf.db.execute
