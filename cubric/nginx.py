from .cubric import Tool


class NGINX(Tool):
    """
    Install nginx vhosts, restart/reload nginx
    """

    def do_reload(self):
        with self.env.sudo():
            self.env.command("service", "nginx", "reload")

    def reload(self):
        self.env.register_task(self.do_reload)

    def install(self, src, name):
        with self.env.sudo():
            self.env.command("ln", "-sf", src,
                             "/etc/nginx/sites-enabled/{name}-nginx.conf"
                             .format(name=name))
        # XXX only if something changed
        self.reload()
