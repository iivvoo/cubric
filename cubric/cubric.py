import paramiko
from contextlib import contextmanager
import os
import time
import shlex

"""
    Look into plumbum for remote execution (does it do remote env?)
    Look in (some) path module -> somepath / 'foo'
"""


class CubricException(Exception):
    pass


class CommandFailedException(CubricException):
    pass


class TemplateException(CubricException):
    pass


def issue_command(transport, command, pause=1):
    chan = transport.open_session()
    chan.exec_command(command)

    buff_size = 1024
    stdout = b""
    stderr = b""

    while not chan.exit_status_ready():
        time.sleep(pause)
        if chan.recv_ready():
            stdout += chan.recv(buff_size)

        if chan.recv_stderr_ready():
            stderr += chan.recv_stderr(buff_size)

    exit_status = chan.recv_exit_status()
    # Need to gobble up any remaining output after program terminates...
    while chan.recv_ready():
        stdout += chan.recv(buff_size)

    while chan.recv_stderr_ready():
        stderr += chan.recv_stderr(buff_size)

    return exit_status, stdout, stderr


class Environment(object):

    def __init__(self, config=None):
        self.cwd = '.'
        self._sudo = False
        self.tasks = []
        self.env = {}
        self.config = config or BaseConfig()

    def set(self, key, var):
        self.env[key] = var

    def register_task(self, task, **args):
        # XXX TODO: check of task not already in queue, store args
        self.tasks.append(task)

    def run_tasks(self):
        for t in self.tasks:
            t()
        self.tasks = []

    def connect(self, host):
        self.client = paramiko.client.SSHClient()
        self.client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        self.client.load_system_host_keys()
        self.client.load_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
        self.client.connect(host)
        self.transport = self.client.get_transport()

    def _run(self, command):
        """ run and handle a command """
        if self._sudo:
            complete_command = "cd {0} && sudo {1}".format(self.cwd, command)
        else:
            complete_command = "cd {0} && {1}".format(self.cwd, command)
        if self.env:
            env = " ".join("{0}={1}".format(k, shlex.quote(v))
                           for (k, v) in self.env.items())
            complete_command = "export {0}\n{1}".format(env, complete_command)
        status, out, err = issue_command(self.transport, complete_command)
        print("===================================")
        print("COMMAND", command)
        print("COMPLETE COMMAND", complete_command)
        print("CWD", self.cwd)
        print("STATUS", status)
        if out:
            print("OUT", out.decode("utf8"))
        if err:
            print("ERR", err.decode("utf8"))

        if status != 0:
            raise CommandFailedException("Aborting, see above")

    def chdir(self, dir):
        self.cwd = os.path.join(self.cwd, dir)

    def mkdir(self, dir, chdir=False):
        self._run("mkdir -p {0}\n".format(dir))
        if chdir:
            self.chdir(dir)

    def chown(self, path, owner=None, group=None):
        if owner or group:
            ownergroup = "{0}:{1}".format(owner or '', group or '')
            self._run("chown {owner} {path}".format(
                path=path, owner=ownergroup))

    def chmod(self, path, mode):
        self._run("chmod {mode} {path}".format(mode=mode, path=path))

    def command(self, command):
        self._run(command)

    @contextmanager
    def sudo(self, user=None):
        oldsudo = self._sudo
        self._sudo = True
        yield
        self._sudo = oldsudo


class DeploymentBase(object):
    requires = ()

    def __init__(self, config=None):
        self.config = config or BaseConfig()

    def deploy(self, hosts):
        for host in hosts:
            env = Environment(self.config)
            for toolclass in self.requires:
                # if toolclass is a tuple, it probably has an alternative name
                try:
                    toolclass, name = toolclass
                    tool = toolclass(env)
                except TypeError:
                    tool = toolclass(env)
                    name = tool.name

                tool.preflight_check()
                setattr(self, name, tool)

            env.connect(host)
            self.run(env)
            env.run_tasks()


class Tool(object):

    def __init__(self, env):
        self.env = env

    @property
    def name(self):
        """ return the name under which the tool will register itself in
            the deployment """

        return self.__class__.__name__.lower()

    def preflight_check(self):
        """ do whatever checks necessary (e.g. remote) to see if the tool
            can run successfully """


class BaseConfig(object):
    """ alternatively make this more dictlike. __iter__ and __getitem__
        is probably sufficient for dict(config) to work """

    @property
    def cubric(self):
        return 'managed by Cubric'  # XXX add timestamp

    def dict(self):
        return {k: getattr(self, k) for k in dir(self) if k[0] != '_'}
