from fabric.api import run

from fabdeploy.task import Task
from fabdeploy.utils import execute_task


class HelloTask(Task):
    def do(self):
        return run("""python -c "print 'Hello'" """)


def test_execute_task():
    hello = HelloTask({'sudo_user': 'vladimir'})
    output = execute_task(hello.run, 'vladimir@localhost')
    assert output == 'Hello'
