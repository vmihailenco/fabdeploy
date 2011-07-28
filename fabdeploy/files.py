import posixpath

from fabric.api import run, sudo, settings, hide

from fabdeploy.utils import split_lines


def list_files(dirpath):
    with settings(hide('running', 'stdout')):
        # -1 - list one file per line
        out = run('ls -1 %s' % dirpath)
    for filename in split_lines(out):
        yield posixpath.join(dirpath, filename)


def read_file(path, use_sudo=False):
    cmd = sudo if use_sudo else run
    with settings(hide('running', 'stdout')):
        out = cmd('cat %s' % path)
    return out
