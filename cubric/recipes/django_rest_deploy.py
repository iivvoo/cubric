import os

from cubric import DeploymentBase, Template, Git, Venv, Supervisor
from cubric import NGINX, File, BaseConfig, Postgres, Ubuntu

pj = os.path.join  # gives us local style joining, may be different from remote
"""
http://jessenoller.com/blog/2009/02/05/ssh-programming-with-paramiko-completely-different

Use Path module for path manipulation? (in stead of pj hack)
"""


class DRFProjectDeployment(DeploymentBase):
    # local install wkhtmltopdf

    requires = (Venv, Template, Supervisor, File, NGINX, Git, Postgres,
                Ubuntu)

    def setup_database(self, env):
        with env.sudo("postgres"):
            self.postgres.user(self.config.db_user, self.config.db_pass)
            self.postgres.database(self.config.db_name, self.config.db_user)

    def git_buildout(self, env):
        self.git.cloneup(self.config.repo, self.config.project,
                         branch=self.config.branch)

        env.chdir(self.config.project)
        self.venv.create() \
            .create() \
            .install("zc.buildout==2.5.0") \
            .install("setuptools")

        env.command("bin/buildout", "-c", self.config.buildoutcfg)

    def django_update(self, env):
        """ update database, etc """
        # XXX Wrap this in some command, with collectstatic, etc
        env.chdir(pj(self.config.instancepath, self.config.project))
        env.command("bin/django", "migrate", "--noinput")
        env.command("bin/django", "collectstatic", "--noinput")

    def restart_redis(self, env):
        with env.sudo():
            env.command("/etc/init.d/redis-server", "restart")

    def setup_huey(self, env):
        # install redis
        # config redis
        # setup supervisor config for huey
        Ubuntu(env).install("redis-server")
        svhueypath = pj(self.config.instancepath, "supervisor-huey.conf")
        command = pj(self.config.instancepath, self.config.project,
                     "bin", "django") + " run_huey"

        self.template \
            .create(src="templates/supervisor-program.conf",
                    dst=svhueypath,
                    args=self.config,
                    program="run_huey",
                    command=command)
        self.template \
            .create(src="templates/redis.conf",
                    dst="/etc/redis/redis.conf",
                    sudo=True,
                    args=self.config)
        if env.last_result:
            env.register_task(lambda: self.restart_redis(env), key="redis-restart")

        self.supervisor.install(svhueypath, "{0}-run_huey".format(
            self.config.projectid))

    def setup_celery(self, env):
        with env.sudo():
            # these commands "fail" if the user / vhost already exist, hence
            # the /bin/true hack which will always give a positive result.
            _env = self.config.environment

            env.command("rabbitmqctl", "add_user", _env, _env, nonzero=True)
            env.command("rabbitmqctl", "add_vhost", _env, nonzero=True)
            env.command("rabbitmqctl", "set_permissions", "-p", _env, _env,
                        '".*"', '".*"', '".*"')
        svcdpath = pj(self.config.instancepath, "supervisor-celeryd.conf")
        svcbpath = pj(self.config.instancepath, "supervisor-celerybeat.conf")
        self.template \
            .create(src="templates/supervisor-celeryd.conf",
                    dst=svcdpath,
                    args=self.config) \
            .create(src="templates/supervisor-celerybeat.conf",
                    dst=svcbpath,
                    args=self.config)
        self.supervisor.install(svcdpath, "{0}-celeryd".format(
            self.config.projectid))
        self.supervisor.install(svcbpath, "{0}-celerybeat".format(
            self.config.projectid))

    def run(self, env):

        self.setup_database(env)

        env.set("DATABASE_URL", self.config.database_url)
        env.set("PROJECT_HOME", pj(self.config.instancepath,
                                   self.config.project))
        env.set("BROKER_URL",
                "ampq://{env}:{env}:5672/{env}"
                .format(env=self.config.environment))

        with env.sudo():
            env.mkdir(self.config.instancepath, chdir=True,
                      owner=self.config.user)

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
        # chaining makes it impossible (?) to do conditional stuff.
        # unless it becomes an extra step in the chain:
        # if tpl.create(...).changed():
        #  .. do stuff if changed
        svcpath = pj(self.config.instancepath, "supervisor.conf")
        nginxpath = pj(self.config.instancepath, "nginx.conf")
        uwsgiconfpath = pj(self.config.instancepath, "uwsgi.conf")
        uwsgicommand = "{0} --ini {1}".format(
                       self.config.uwsgi, uwsgiconfpath)
        self.template \
            .create(src="templates/supervisor-program.conf",
                    dst=svcpath,
                    args=self.config,
                    command=uwsgicommand,
                    program="uwsgi") \
            .create(src="templates/uwsgi.conf",
                    dst=pj(self.config.instancepath, "uwsgi.conf"),
                    args=self.config) \
            .create(src="templates/nginx-drf.conf",
                    dst=nginxpath,
                    args=self.config)
        self.supervisor.install(svcpath, "{0}-uwsgi".format(
            self.config.projectid))

        # self.setup_celery(env)
        self.setup_huey(env)

        self.nginx.install(nginxpath, self.config.projectid)


class DRFProjectConfig(BaseConfig):
    environment = "dev"
    projectname = "acmeproject"
    branch = "master"
    buildoutcfg = "development.cfg"

    @property
    def projectid(self):
        return "{0}-{1}".format(self.projectname, self.environment)
