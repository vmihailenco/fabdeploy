from fabric.api import run

from fabdeploy.task import Task


class HelloTask(Task):
    def do(self):
        return run("""python -c "print 'Hello'" """)


def test_execute_task():
    hello = HelloTask()
    with hello.tmp_conf({'address': 'vladimir@localhost',
                         'sudo_user': 'vladimir'}):
#                        abort_on_prompts=True):
        output = hello.run()
    assert output == 'Hello'
