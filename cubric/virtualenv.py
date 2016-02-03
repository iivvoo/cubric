from .cubric import Tool


class Venv(Tool):

    def create(self, path=".", force=False):
        if force:
            self.env.command("virtualenv --system-site-packages "
                             "-p /usr/bin/python3.4 {path}".format(path=path))
        else:
            self.env.command("test -e {path}/bin/activate_this.py || "
                             "virtualenv --system-site-packages "
                             "-p /usr/bin/python3.4 {path}".format(path=path))
        return self

    def install(self, package):
        self.env.command(
            "bin/pip install --upgrade {package}".format(package=package))
        return self
