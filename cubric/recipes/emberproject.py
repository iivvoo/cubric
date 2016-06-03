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
        self.git.cloneup(self.config.repo, self.config.project)

    def run(self, env):
        self.file.removed(self.config.project)
        self.sync_repo(env)
        with env.chdir(self.config.project):
            print("Using node:")
            env.command("node", "-v")
            env.command("npm", "install")
            env.command("bower", "install")
            env.command("ember", "build", "--env={}".format(self.ember_env))


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

        with env.sudo():
            env.mkdir(self.config.instancepath, chdir=True,
                      owner=self.config.user)
        # Not usable, works remotely not local!
        # print("Hash", self.git.shorthash(self.config.project))

        tsfolder = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        for d in ("logs", tsfolder):
            env.mkdir(self.config.instancepath / d)
        plumbum.path.utils.copy(Path(self.config.project) / 'dist',
                                env.host.path(self.config.instancepath
                                              / tsfolder))
        self.file.present(self.config.instancepath / tsfolder,
                          target=self.config.instancepath / 'www',
                          type=File.LINK)
        self.template.create(src="templates/emberapp-nginx.conf",
                             dst=self.config.instancepath / 'nginx.conf',
                             args=self.config)
        self.nginx.install(self.config.instancepath / 'nginx.conf',
                           self.config.projectid)
