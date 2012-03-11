from fabric.api import run

from fabdeploy.task import Task


def test_execute_task():
    class HelloTask(Task):
        def do(self):
            return run("""python -c "print 'Hello'" """)

    hello = HelloTask()
    with hello.tmp_conf(
        {'sudo_user': 'vladimir'},
        abort_on_prompts=True):
        output = hello.run()
    assert output == 'Hello'
