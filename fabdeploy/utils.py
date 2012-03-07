import posixpath
from functools import wraps
from contextlib import contextmanager

from fabric.api import env, sudo, cd, prefix, abort
from fabric import network
from fabric.contrib.files import upload_template


@contextmanager
def host(host_string):
    old_host_string = env.host_string
    env.host_string = host_string

    yield

    env.host_string = old_host_string


@contextmanager
def user(username):
    old_username, host, port = network.normalize(env.host_string)
    env.host_string = network.join_host_strings(username, host, port)

    yield

    env.host_string = network.join_host_strings(old_username, host, port)


def with_user(username):
    """
    Decorator. Runs fabric command as specified user. It is most useful to
    run commands that require root access to server.
    """
    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            with user(username):
                return func(*args, **kwargs)
        return inner
    return decorator


@contextmanager
def sudo_user():
    with user(env.conf.sudo_user):
        yield


def with_sudo_user():
    return with_user(env.conf.sudo_user)


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
    Decorator. Use it to perform actions inside remote django dir
    (that's a folder where :file:`manage.py` resides) with
    virtualenv activated::

        from fabric.api import *
        from fab_deploy.utils import inside_django

        @inside_django
        def cleanup():
            # the current dir is a django source dir and
            # virtualenv is activated
            run('python manage.py cleanup')

    """
    @wraps(func)
    def inner(*args, **kwargs):
        with cd(env.conf.django_path):
            with virtualenv():
                return func(*args, **kwargs)
    return inner


def upload_config_template(
    name, to=None, context=None, skip_unexistent=False, **kwargs):
    config_template = env.conf.config_template_lpath(name)
    if to is None:
        to = posixpath.join(env.conf.etc_path, name)
    if context is None:
        context = env.conf

    if config_template is None:
        if skip_unexistent:
            return
        abort('Config template "%s" is not found.' % name)

    upload_template(
        config_template, to, context, use_jinja=True, **kwargs)


def upload_init_template(name, **kwargs):
    template = 'init/' + name
    to = posixpath.join('/etc/init', name)
    upload_config_template(template, to, use_sudo=True, **kwargs)
    sudo('chown --recursive root:root ' + to)


# TODO: move to conf
def unprefix_conf(conf, namespaces):
    for ns in namespaces:
        for key in conf.keys():
            if key.startswith(ns):
                conf[key[len(ns):]] = conf[key]


# TODO: move to conf
def home_path(user):
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
