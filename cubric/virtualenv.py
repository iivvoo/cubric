from .cubric import Tool, NonZero


class Venv(Tool):

    def create(self, path=".", force=False):
        if force:
            self.env.command("virtualenv", "--system-site-packages"
                             "-p", "/usr/bin/python3.4", path)
        else:
            try:
                self.env.command("test", "-e", path + "/bin/activate_this.py")
            except NonZero:
                self.env.command("virtualenv", "--system-site-packages",
                                 "-p", "/usr/bin/python3.4", path)
        return self

    def install(self, package):
        self.env.command("bin/pip", "install", "--upgrade", package)
        return self
