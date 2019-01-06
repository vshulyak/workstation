from fabric.api import env, execute, get, local, put, run, settings, hide, cd
from fabric.colors import green, red, yellow
from fabric.contrib.files import exists
from fabric.decorators import parallel, roles
from fabric.operations import sudo, open_shell

from .setup import get_instance


def jupyter():
    """
    Launch Jupyter instance on the remote machine
    """
    instance = get_instance(state='running')

    # hide fab logging info
    env.output_prefix = False

    if not instance:
        print(red("Instance is not running, run 'setup' first" % env))
        exit(1)

    print(green("Connecting to instance {} at {}".format(instance.instance_type,
                                                         instance.public_ip_address)))
    execute(_launch_docker, instance=instance, hosts=[instance.public_ip_address])


def tunnel():
    """
    Setup a tunnel to the running Jupyter process on the remote machine
    """
    instance = get_instance(state='running')

    # hide fab logging info
    env.output_prefix = False

    if not instance:
        print(red("Instance is not running, run 'setup' first" % env))
        exit(1)

    print(green("Tunneling to instance {} at {}".format(instance.instance_type,
                                                        instance.public_ip_address)))
    ctx = dict(
        user=env.user,
        host=instance.public_ip_address
    )
    cmd = "ssh -fN -o ExitOnForwardFailure=yes -L 8888:localhost:8888 {user}@{host}".format(**ctx)

    # kill possibly existing one
    with hide('warnings'), settings(warn_only=True):
        if local("pgrep -f \"{cmd}\"".format(cmd=cmd)).return_code == 0:
            local("pkill -f \"{cmd}\"".format(cmd=cmd))

    # run new one
    local(cmd)


def shell():
    instance = get_instance(state='running')

    # hide fab logging info
    env.output_prefix = False

    if not instance:
        print(red("Instance is not running, run 'setup' first" % env))
        exit(1)

    print(green("Connecting to instance {} at {}".format(instance.instance_type,
                                                         instance.public_ip_address)))

    def _open_shell(instance):
        open_shell()

    execute(_open_shell, instance=instance, hosts=[instance.public_ip_address])


def _launch_docker(instance):
    with cd("~/project"):
        run("docker-compose up")


"""
https://stackoverflow.com/questions/5609192/how-to-set-up-tmux-so-that-it-starts-up-with-specified-windows-opened/5753059

tmux new-session \; \
  send-keys 'cd ~/project && docker-compose up' C-m \; \
  split-window -v -p 75 \; \
  split-window -h -p 30 \; \
  send-keys 'top' C-m \; \
  select-pane -t 1 \; \
  split-window -v \; \
  send-keys 'watch -n1 free -h' C-m \;

"""
