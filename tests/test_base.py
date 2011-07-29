from fabdeploy.base import setup_conf


def test_update_conf():
    conf = setup_conf(dict(address='fabdeploy@localhost'))

    assert conf.user == 'fabdeploy'
    assert conf.host == 'localhost'
    assert conf.home_dir == '/home/fabdeploy'
    assert conf.src_dir == '/home/fabdeploy/src/fabdeploy'
    assert conf.project_dir == '/home/fabdeploy/src/fabdeploy'
    assert conf.django_dir == '/home/fabdeploy/src/fabdeploy'
    assert conf.env_dir == '/home/fabdeploy/envs/fabdeploy'
    assert conf.etc_dir == '/home/fabdeploy/envs/fabdeploy/etc'
    assert conf.var_dir == '/home/fabdeploy/envs/fabdeploy/var'
    assert conf.log_dir == '/home/fabdeploy/envs/fabdeploy/var/log'
    assert conf.backups_dir == '/home/fabdeploy/envs/fabdeploy/var/backups'

    assert conf.time_format == '%Y.%m.%d-%H.%M'
    assert conf.sudo_user == 'root'
    assert conf.server_name == 'localhost'
    assert conf.server_admin == 'admin@localhost'

    assert conf.db_name == 'fabdeploy'
    assert conf.db_user == 'fabdeploy'
    assert conf.db_password == 'fabdeploy'
    assert conf.db_host == 'localhost'
