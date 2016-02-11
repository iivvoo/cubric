from contextlib import contextmanager
import os
import time
import shlex
from plumbum.machines.paramiko_machine import ParamikoMachine
from plumbum import local, ProcessExecutionError

"""
    Look into plumbum for remote execution (does it do remote env?)
    Look in (some) path module -> somepath / 'foo'
"""


class CubricException(Exception):
    pass


class CommandFailedException(CubricException):
    pass


class NonZero(CubricException):
    pass


class TemplateException(CubricException):
    pass


class UndoChdir:
    """
        context manager that can restore the old cwd on __exit__
    """
    def __init__(self, env, old):
        self.env = env
        self.old = old

    def __enter__(self):
        pass

    def __exit__(self, t, v, tb):
        print("Resetting cwd to", self.old)
        self.env.host.cwd.chdir(self.old)


class Environment(object):

    def __init__(self, config=None):
        self._sudo = False
        self.tasks = []
        self.env = {}
        self.config = config or BaseConfig()

    def set(self, key, var):
        self.host.env[key] = var

    def register_task(self, task, **args):
        # XXX TODO: check of task not already in queue, store args
        self.tasks.append(task)

    def run_tasks(self):
        for t in self.tasks:
            t()
        self.tasks = []

    def connect(self, host):
        self.host = host

    def disconnect(self):
        if self.host != local:
            self.host.close()
        self.host = None

    def issue_command(self, command, *args, nonzero=False):

        kw = {}

        if nonzero:
            kw['retcode'] = None

        try:
            cmd = self.host[command]

            if self._sudo:
                return self.host["sudo"][cmd](*args, **kw)
            return cmd(*args, **kw)
        except ProcessExecutionError:
            raise NonZero()

    def _run(self, command, *args, nonzero=False):
        """ run and handle a command """
        print("===================================")
        print("COMMAND", command, args)
        if nonzero:
            print("NONZERO: Ignoring return codes")
        print("REPORTED CWD", self.host.cwd)
        out = self.issue_command(command, *args, nonzero=nonzero)
        if out:
            print("OUT", out)

    def chdir(self, dir):
        oldcwd = self.host.cwd
        self.host.cwd.chdir(dir)
        return UndoChdir(self, oldcwd)

    def mkdir(self, dir, chdir=False):
        self._run("mkdir", "-p", dir)
        if chdir:
            self.chdir(dir)

    def chown(self, path, owner=None, group=None):
        if owner or group:
            ownergroup = "{0}:{1}".format(owner or '', group or '')
            self._run("chown", ownergroup, path)

    def chmod(self, path, mode):
        self._run("chmod", mode, path)

    def command(self, command, *args, nonzero=False):
        self._run(command, *args, nonzero=nonzero)

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
            print("Deploying to host {0}".format(host))
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

            if host == "_localhost_":
                env.connect(local)
            else:
                remote = ParamikoMachine(host)
                env.connect(remote)

            self.run(env)
            env.run_tasks()
            env.disconnect()
            print("Host {0} complete".format(host))


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
