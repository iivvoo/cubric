from .cubric import Tool


class Git(Tool):

    def cloneup(self, repo, folder, branch="master", tag=None, commit=None):
        """ clone or update a repo
            TODO: if folder is None -> derive from repo
        """
        args = dict(folder=folder, repo=repo, branch=branch, tag=tag,
                    commit=commit)
        self.env.command(
            "test -x {folder} || git clone {repo} {folder}".format(**args))
        if tag:
            self.env.command(
                "cd {folder} && git pull && git checkout {tag}".format(**args))
        elif commit:
            self.env.command(
                "cd {folder} && git pull && "
                "git checkout {commit}".format(**args))
        else:
            self.env.command(
                "cd {folder} && git pull "
                "&& git checkout {branch} "
                "&& git merge origin/{branch}".format(**args))
        return self
