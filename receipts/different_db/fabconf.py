from fabdeploy import api
from fabdeploy.api import DefaultConf


class DevConf(DefaultConf):
    address = 'user@localhost'
    db = getattr(api, 'mysql')


class ProdConf(DefaultConf):
    address = 'user@localhost'
    db = getattr(api, 'postgres')
