from fabdeploy.containers import DefaultConf


def test_update_conf():
    conf = DefaultConf()
    conf.address = 'fabdeploy@localhost'

    assert conf.user == 'fabdeploy'
    assert conf.host == 'localhost'
    assert conf.instance_name == 'fabdeploy'

    assert conf.home_path == '/home/fabdeploy'
    assert conf.releases_path == '/home/fabdeploy/releases'
    assert conf.release_path == '%s/%s' % (conf.releases_path, conf.release)
    assert conf.project_path == conf.release_path
    assert conf.django_path == conf.release_path
    assert conf.shared_path == conf.home_path + '/shared'
    assert conf.env_path == conf.release_path + '/env'
    assert conf.etc_path == conf.shared_path + '/etc'
    assert conf.var_path == conf.shared_path + '/var'
    assert conf.log_path == conf.var_path + '/log'
    assert conf.backup_path == conf.var_path + '/backup'

    assert conf.time_format == '%Y.%m.%d-%H.%M.%S'
    assert conf.sudo_user == 'root'
    assert conf.server_name == 'localhost'
    assert conf.server_admin == 'admin@localhost'

    assert conf.db_name == 'fabdeploy'
    assert conf.db_user == 'fabdeploy'
    assert conf.db_password == 'fabdeploy'
    assert conf.db_host == 'localhost'
