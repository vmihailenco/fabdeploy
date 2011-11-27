import posixpath

from fabric.api import run, settings, hide, sudo

from .utils import split_lines


def list_files(dirpath):
    with settings(hide('running', 'stdout')):
        # -1 - list one file per line
        out = run('ls -1 %s' % dirpath)
    for filename in split_lines(out):
        yield posixpath.join(dirpath, filename)


def read_file(path, use_sudo=False, shell=True):
    cmd = sudo if use_sudo else run
    with settings(hide('running', 'stdout')):
        out = cmd('cat %s' % path, shell=shell)
    return out


def exists(path, use_sudo=False, verbose=False, shell=True):
    """
    Return True if given path exists on the current remote host.

    If ``use_sudo`` is True, will use `sudo` instead of `run`.

    `exists` will, by default, hide all output (including the run line, stdout,
    stderr and any warning resulting from the file not existing) in order to
    avoid cluttering output. You may specify ``verbose=True`` to change this
    behavior.
    """
    func = use_sudo and sudo or run
    cmd = 'test -e "%s"' % path
    # If verbose, run normally
    if verbose:
        with settings(warn_only=True):
            return not func(cmd, shell=shell).failed
    # Otherwise, be quiet
    with settings(hide('everything'), warn_only=True):
        return not func(cmd, shell=shell).failed
