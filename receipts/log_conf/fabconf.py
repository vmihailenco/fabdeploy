from fabdeploy.api import DefaultConf


class ProdConf(DefaultConf):
    my_task__log_path = '/var/log/my_task'
