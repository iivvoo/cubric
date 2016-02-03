from .cubric import Tool


class Supervisor(Tool):
    """
    Install supervisor entries, restart/reload supervisor and/or individual
    tasks
    """

    def do_reload(self):
        with self.env.sudo():
            self.env.command("supervisorctl update")

    def reload(self):
        self.env.register_task(self.do_reload)

    def install(self, src, name):
        with self.env.sudo():
            self.env.command("ln -sf {src} "
                             " /etc/supervisor/conf.d/{name}-supervisor.conf"
                             .format(src=src, name=name))
        # XXX only if something changed
        self.reload()
