from fabdeploy.base import setup_conf


def test_update_conf():
    conf = setup_conf(dict(
        address='fabdeploy@localhost',
        os=None,
    ))

    assert conf.user == 'fabdeploy'
    assert conf.host == 'localhost'
    assert conf.instance_name == 'fabdeploy'

    assert conf.home_path == '/home/fabdeploy'
    assert conf.src_path == '/home/fabdeploy/src/fabdeploy'
    assert conf.project_path == '/home/fabdeploy/src/fabdeploy'
    assert conf.django_path == '/home/fabdeploy/src/fabdeploy'
    assert conf.env_path == '/home/fabdeploy/envs/fabdeploy'
    assert conf.etc_path == '/home/fabdeploy/envs/fabdeploy/etc'
    assert conf.var_path == '/home/fabdeploy/envs/fabdeploy/var'
    assert conf.log_path == '/home/fabdeploy/envs/fabdeploy/var/log'
    assert conf.backups_path == '/home/fabdeploy/envs/fabdeploy/var/backups'

    assert conf.time_format == '%Y.%m.%d-%H.%M'
    assert conf.sudo_user == 'root'
    assert conf.server_name == 'localhost'
    assert conf.server_admin == 'admin@localhost'

    assert conf.db_name == 'fabdeploy'
    assert conf.db_user == 'fabdeploy'
    assert conf.db_password == 'fabdeploy'
    assert conf.db_host == 'localhost'
