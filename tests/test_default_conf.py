from fabdeploy.containers import DefaultConf


def test_update_conf():
    conf = DefaultConf()
    conf.address = 'fabdeploy@localhost'
    conf.os = None

    assert conf.user == 'fabdeploy'
    assert conf.host == 'localhost'
    assert conf.instance_name == 'fabdeploy'

    version = conf.version
    version_path = '/home/fabdeploy/%s' % version

    assert conf.home_path == '/home/fabdeploy'
    assert conf.version_path == version_path
    assert conf.src_path == version_path + '/src'
    assert conf.project_path == version_path + '/src'
    assert conf.django_path == version_path + '/src'
    assert conf.env_path == version_path + '/env'
    assert conf.etc_path == version_path + '/env/etc'
    assert conf.var_path == version_path + '/env/var'
    assert conf.log_path == version_path + '/env/var/log'
    assert conf.backup_path == version_path + '/env/var/backup'

    assert conf.time_format == '%Y.%m.%d-%H.%M.%S'
    assert conf.sudo_user == 'root'
    assert conf.server_name == 'localhost'
    assert conf.server_admin == 'admin@localhost'

    assert conf.db_name == 'fabdeploy'
    assert conf.db_user == 'fabdeploy'
    assert conf.db_password == 'fabdeploy'
    assert conf.db_host == 'localhost'
