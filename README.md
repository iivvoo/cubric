# Cubric

Cubric attempts to make creating deployments easier. It lives somewhere between
Fabric and Ansible: it aims for Fabric's programmability and Ansible's idempotent
declarative modules / commands, all while being high level and pythonic.

**WARNING** Cubric is incomplete, unstable, very alpha and not usable for anyone
but me. What are you doing here anyway?

## Sample

A code snippet says more than a thousand words.

    class DjangoProjectDeployment(DeploymentBase):

        requires = (Venv, Template, Supervisor, File, NGINX, Git, Postgres)

        def setup_database(self, env):
            self.postgres.user(self.config.db_user, self.config.db_pass)
            self.postgres.database(self.config.db_name, self.config.db_user)

        def git_buildout(self, env):
            self.git.cloneup(self.config.repo, self.config.project)

            env.chdir(self.config.project)
            self.venv.create() \
                .create() \
                .install("zc.buildout==2.5.0") \
                .install("setuptools")

            env.command("bin/buildout", "-c", "development.cfg")

        def django_update(self, env):
            """ update database, etc """
            env.chdir(pj(self.config.instancepath, self.config.project))
            env.command("bin/django", "migrate")

        def run(self, env):

            self.setup_database(env)

            env.set("DATABASE_URL", self.config.database_url)

            env.mkdir(self.config.instancepath, chdir=True)

            self.git_buildout(env)

            self.django_update(env)

            env.chdir(self.config.instancepath)

            for d in ("logs", "run", "static", "media", "www"):
                env.mkdir(pj(self.config.instancepath, d))
            with env.sudo():
                self.file.present(pj(self.config.instancepath, "run"),
                                  type=File.DIR,
                                  mode="2770",
                                  group="www-data")

            svcpath = pj(self.config.instancepath, "supervisor.conf")
            nginxpath = pj(self.config.instancepath, "nginx.conf")
            self.template \
                .create(src="templates/supervisor.conf",
                        dst=svcpath,
                        args=self.config) \
                .create(src="templates/uwsgi.conf",
                        dst=pj(self.config.instancepath, "uwsgi.conf"),
                        args=self.config) \
                .create(src="templates/nginx.conf",
                        dst=nginxpath,
                        args=self.config)
            self.supervisor.install(svcpath, self.config.projectid)

            self.nginx.install(nginxpath, self.config.projectid)

The class above will, if configured/invoked correctly git clone/update a repo,
run buildout, setup database, supervisor, nginx and uwsgi on a remote host.
