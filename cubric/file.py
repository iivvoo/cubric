import os
import tempfile

from plumbum.path.utils import copy

from .cubric import Tool, NonZero


class File(Tool):
    DIR = 1
    FILE = 2
    LINK = 3

    def _fixattrs(self, file, mode, user, group):
        if mode:
            self.env.chmod(file, mode)
        if user or group:
            self.env.chown(file, user, group)

    def present(self, path, type=DIR, mode=None, user=None, group=None,
                target=None):
        if type == File.LINK:
            if target:
                self.env.command("ln", "-sfn", path, target)
            else:
                self.env.command("ln", "-sfn", path)
            return self
        if type == File.DIR:
            self.env.mkdir(path)
        elif type == File.FILE:
            try:
                self.env.command("test", "-e", path)
            except NonZero:
                self.env.command("touch", path)
        self._fixattrs(path, mode, user, group)
        return self

    def removed(self, path):
        if not os.path.exists(path):
            return self
        self.env.command("rm", "-rf", path)
        return self

    def create(self, file, content, mode=None, user=None, group=None):
        """ create a file with content """
        self.env.shell("echo '{0}' > {1}".format(content, file))
        self._fixattrs(file, mode, user, group)
        return self

    def copy(self, src, dst, mode=None, user=None, group=None):
        dst = self.env.host.path(dst)
        copy(src, dst)
        self._fixattrs(dst, mode, user, group)
        return self

    def copy_owner(self, src, dst, mode=None, user=None, group=None):
        """ copy with sudo """
        tmpname = "/tmp/{0}".format(next(tempfile._get_candidate_names()))

        copy(src, self.env.host.path(tmpname))
        with self.env.sudo():
            self.env.command("mv", tmpname, dst)
            # if sudo to a specific user, fix ownership
            if self.env._sudo:
                self.env.chown(dst, self.env._sudouser)
            elif user:
                self.env.chown(dst, user)