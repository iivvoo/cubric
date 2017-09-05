from cubric import DeploymentBase
from cubric import Git, File, Template, NGINX
from path import Path
import plumbum
import datetime


class EmberLocalBuild(DeploymentBase):
    requires = (Git, File)

    _ember_env = "demo"

    @property
    def ember_env(self):
        try:
            return self.config.ember_env
        except AttributeError:
            return self._ember_env

    def sync_repo(self, env):
        self.git.cloneup(self.config.repo, self.config.project,
                         self.config.branch)

    def run(self, env):
        self.file.removed(self.config.project)
        self.sync_repo(env)
        with env.chdir(self.config.project):
            print("Using node:")
            env.command("node", "-v")
            use_yarn = False
            use_bower = True
            try:
                use_yarn = self.config.yarn
            except AttributeError:
                pass
            try:
                use_bower = self.config.bower
            except AttributeError:
                pass

            if use_yarn:
                env.command("npm", "install", "-g", "yarn")
                if use_bower:
                    env.command("npm", "install", "-g", "bower")
                env.command("yarn", "install")
            else:
                env.command("npm", "install")
            if use_bower:
                env.command("bower", "install", "--allow-root")
            env.command("node_modules/.bin/ember", "build", "--env={}".format(self.ember_env))


class EmberDeploy(DeploymentBase):
    requires = (Git, File, Template, NGINX)

    def run(self, env):
        """
            - Create remote instance folder
            - Create folder based on commit hash
            - Recursive copy dist/
            - Symlink
            - Setup / update nginx
        """

        logpath = self.config.instancepath / 'logs'
        with env.sudo():
            env.mkdir(logpath, owner=self.config.user)
            env.mkdir(self.config.instancepath, chdir=True,
                      owner=self.config.user)

        # Not usable, works remotely not local!
        # print("Hash", self.git.shorthash(self.config.project))

        tsfolder = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        tmpfile = Path("/tmp") / tsfolder

        plumbum.path.utils.copy(Path(self.config.project) / 'dist',
                                env.host.path(tmpfile))
        with env.sudo():
            env.chown(tmpfile, owner=self.config.user, recursive=True)
            env.move(tmpfile, self.config.instancepath / tsfolder)

        with env.sudo(self.config.user):
            for d in ("logs", tsfolder):
                env.chown(self.config.instancepath / d, owner=self.config.user)
            self.file.present(self.config.instancepath / tsfolder,
                              target=self.config.instancepath / 'www',
                              type=File.LINK)
            self.template.create(src="templates/emberapp-nginx.conf",
                                 dst=self.config.instancepath / 'nginx.conf',
                                 args=self.config)
            self.nginx.install(self.config.instancepath / 'nginx.conf',
                               self.config.projectid)
