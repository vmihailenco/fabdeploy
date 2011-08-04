import re
import posixpath
from functools import wraps
from contextlib import contextmanager

from fabric.api import env, cd, run, prefix, abort, settings
from fabric import network
from fabric.utils import puts
from fabric.operations import _handle_failure
from fabric.network import disconnect_all
from fabric.contrib.files import upload_template


DETECTION_ERROR_MESSAGE = """
OS detection failed. This probably means your OS is not
supported by django-fab-deploy. If you really know what
you are doing, set env.conf.OS variable to desired OS
name in order to bypass this error message.
If you believe the OS is supported but the detection
fails or you want to get your OS supported, please fire an issue at
https://bitbucket.org/kmike/django-fab-deploy/issues/new
"""


def codename(distname, version, id):
    patterns = [
        ('squeeze', ('debian', '^6', '')),
        ('lenny', ('debian', '^5', '')),
        ('natty', ('Ubuntu', '^11.04', '')),
        ('maverick', ('Ubuntu', '^10.10', '')),
        ('lucid', ('Ubuntu', '^10.04', '')),
    ]
    for name, p in patterns:
        if (re.match(p[0], distname) and
                re.match(p[1], version) and
                re.match(p[2], id)):
            return name


def detect_os(address):
    with host(address):
        output = run('python -c "import platform; print platform.dist()"')

    name = codename(*eval(output))
    if name is None:
        abort(DETECTION_ERROR_MESSAGE)
        return

    puts('OS %s is detected' % name)
    return name


@contextmanager
def host(host_string):
    old_host_string = env.host_string
    env.host_string = host_string

    yield

    env.host_string = old_host_string


def run_as(user):
    """
    Decorator. Runs fabric command as specified user. It is most useful to
    run commands that require root access to server.
    """
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            old_user, host, port = network.normalize(env.host_string)
            env.host_string = network.join_host_strings(user, host, port)
            result = func(*args, **kwargs)
            env.host_string = network.join_host_strings(old_user, host, port)
            return result
        return inner
    return decorator


def run_as_sudo(func):
    """
    Decorator. By default all commands are executed as user without
    sudo access for security reasons. Use this decorator to run fabric
    command as user with sudo access (:attr:`env.conf.SUDO_USER`)::

        from fabric.api import run
        from fab_deploy import utils

        @utils.run_as_sudo
        def aptitude_update():
            sudo('aptitude update')
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return run_as(env.conf.sudo_user)(func)(*args, **kwargs)
    return wrapper


def virtualenv():
    """
    Context manager. Use it for perform actions with virtualenv activated::

        with virtualenv():
            # virtualenv is active here

    """
    return prefix('source %s/bin/activate' % env.conf.env_path)


def inside_virtualenv(func):
    """
    Decorator. Use it for perform actions with virtualenv activated::

        @inside_virtualenv
        def my_command():
            # virtualenv is active here

    """
    @wraps(func)
    def inner(*args, **kwargs):
        with virtualenv():
            return func(*args, **kwargs)
    return inner


def inside_project(func):
    """
    Decorator. Use it to perform actions inside remote source dir
    (repository root) with virtualenv activated.
    """
    @wraps(func)
    def inner(*args, **kwargs):
        with cd(env.conf.project_path):
            return func(*args, **kwargs)
    return inner


def inside_django(func):
    """
    Decorator. Use it to perform actions inside remote project dir
    (that's a folder where :file:`manage.py` resides) with
    virtualenv activated::

        from fabric.api import *
        from fab_deploy.utils import inside_project

        @inside_project
        def cleanup():
            # the current dir is a project source dir and
            # virtualenv is activated
            run('python manage.py cleanup')

    """
    @wraps(func)
    def inner(*args, **kwargs):
        with cd(env.conf.django_path):
            with virtualenv():
                return func(*args, **kwargs)
    return inner


def upload_config_template(name, to=None, context=None, skip_unexistent=False,
                           **kwargs):
    config_template = env.conf.config_templates_lpath_getter(name)
    if to is None:
        to = posixpath.join(env.conf.etc_path, name)
    if context is None:
        context = env.conf

    if config_template is None:
        if skip_unexistent:
            return
        _handle_failure('Config template "%s" is not found' % name)

    upload_template(config_template, to, context, use_jinja=True,
                    **kwargs)


def unprefix_conf(conf, prefixes):
    for prefix in prefixes:
        for key in conf.copy():
            if key.startswith(prefix):
                conf[key[len(prefix):]] = conf[key]
    return conf


def get_home_path(user):
    if user == 'root':
        return '/root'
    else:
        return posixpath.join('/home', user)


def split_lines(value):
    lines = value.split('\n')
    for line in lines:
        yield line.rstrip('\r')


class cached_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, type=None):
        if obj is None:
            return self

        obj.__dict__[self.func.__name__] = value = self.func(obj)
        return value


def execute_task(func, host, *args, **kwargs):
    """Execute task in non-fabric environment (library usage)"""
    try:
        with settings(host_string=host, abort_on_prompts=True):
            return func(*args, **kwargs)
    finally:
        disconnect_all()
