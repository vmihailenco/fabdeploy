import multiprocessing

from fabdeploy import system


def test_cpu_count():
    cpu_count = multiprocessing.cpu_count()
    with system.cpu_count.tmp_conf():
        assert system.cpu_count.cpu_count() == cpu_count


def test_os_codename():
    with system.os_codename.tmp_conf():
        assert system.os_codename.os_codename() != None
