from .cubric import Tool, NonZero


class Git(Tool):

    def cloneup(self, repo, folder, branch="master", tag=None, commit=None):
        """ clone or update a repo
            TODO: if folder is None -> derive from repo
        """
        try:
            self.env.command("test", "-x", folder)
        except NonZero:
            self.env.command("git", "clone", repo, folder)

        with self.env.chdir(folder):

            if tag:
                self.env.command("git", "pull")
                self.env.command("git", "checkout", tag)
            elif commit:
                self.env.command("git", "pull")
                self.env.command("git", "checkout", commit)
            else:
                self.env.command("git", "pull")
                self.env.command("git", "checkout", branch)
                self.env.command("git", "merge", "origin/" + branch)
        return self
