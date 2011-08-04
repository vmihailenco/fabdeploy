from fabric.api import run

from fabdeploy.task import Task
from fabdeploy.utils import execute_task


class HelloTask(Task):
    def do(self):
        return run("""python -c "print 'Hello'" """)


def test_execute_task():
    hello = HelloTask()
    with hello.custom_conf({'address': 'vladimir@localhost',
                            'sudo_user': 'vladimir'}):
        output = hello.run()
    assert output == 'Hello'
