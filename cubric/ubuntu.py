from .cubric import Tool


class Ubuntu(Tool):

    def update(self):
        with self.env.sudo():
            self.env.command("apt-get update -y")
        return self

    def install(self, package):
        with self.env.sudo():
            self.env.command(
                "apt-get install -y {package}".format(package=package))
        return self
