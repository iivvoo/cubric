from .cubric import Tool, NonZero
from .file import  File


class Users(Tool):

    def create(self, username, sudo=False):
        try:
            self.env.command("adduser", username, "--disabled-password",
                             "--quiet", "--gecos", "{0} account".format(username))
        except NonZero:
            pass

        if sudo:
            self.env.command("adduser", username, "sudo")
        return self

    def add_pubkey(self, user, keyfile):
        data = open(keyfile, "r").read().strip()
        dir = "/home/{0}/.ssh/".format(user)
        path = dir + '/authorized_keys'
        File(self.env).present(dir, type=File.DIR, mode="700", user=user)
        self.env.shell("grep '{0}' {1} || "
                       "echo '{0}' >> {1}".format(data, path))

    def add_privkey(self, user, keyfile, dst="id_rsa"):
        file = File(self.env)
        dir = "/home/{0}/.ssh/".format(user)

        file.copy_owner(keyfile, dir + dst, mode="0600", user=user)
        return self

    def add_knownhosts(self, user, hostsfile, dst="known_hosts"):
        file = File(self.env)
        dir = "/home/{0}/.ssh/".format(user)

        file.copy_owner(hostsfile, dir + dst, mode="0600", user=user)
        return self
