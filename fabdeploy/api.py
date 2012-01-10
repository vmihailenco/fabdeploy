from . import fabd, system, git, version, virtualenv, nginx, django, pip, \
    postgres, mysql, supervisor, users, ssh, tar, gunicorn, uwsgi, rabbitmq, \
    apache
from .base import setup_fabdeploy
from .containers import conf
from .task import Task
