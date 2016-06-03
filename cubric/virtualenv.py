from .cubric import Tool, NonZero


class Venv(Tool):
    _python = "/usr/bin/python3.4"

    def __init__(self, venv, python=None):
        super().__init__(venv)
        if python:
            self._python = python

    @property
    def python(self):
        try:
            return self.env.config.python
        except AttributeError:
            return self._python

    def create(self, path=".", force=False):
        if force:
            self.env.command("virtualenv", "--system-site-packages"
                             "-p", self.python, path)
        else:
            try:
                self.env.command("test", "-e", path + "/bin/activate_this.py")
            except NonZero:
                self.env.command("virtualenv", "--system-site-packages",
                                 "-p", self.python, path)
        return self

    def install(self, package):
        self.env.command("bin/pip", "install", "--upgrade", package)
        return self
