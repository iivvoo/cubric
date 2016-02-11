from .cubric import Tool, NonZero


class File(Tool):
    DIR = 1
    FILE = 2

    def present(self, path, type=DIR, mode=None, user=None, group=None):
        if type == File.DIR:
            self.env.mkdir(path)
        elif type == File.FILE:
            try:
                self.env.command("test", "-e", path)
            except NonZero:
                self.env.command("touch", path)
        if mode:
            self.env.chmod(path, mode)
        if user or group:
            self.env.chown(path, user, group)
        return self
