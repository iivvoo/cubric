from hashlib import md5
from .cubric import Tool, NonZero


class Postgres(Tool):
    """
        Assumes remote execution user (e.g. sudo) is postgres superuser

    """
    PRESENT = 1
    REMOVED = 2

    def pgexecute(self, command, nonzero=False):
        # some quote escaping magic.
        # command = command.replace("'", r"'\''")
        self.env.command("psql", "postgres", "-c", command, nonzero=nonzero)

    def user(self, username, password=None, superuser=False, state=PRESENT):

        if state == Postgres.REMOVED:
            self.pgexecute('DROP ROLE IF EXISTS "{0}"'.format(username))
        else:
            # this may produce an SQL error if the user exists.
            try:
                self.pgexecute('CREATE ROLE "{0}"  '.format(username))
            except NonZero:
                pass
            if password:
                pghash = md5(password.encode("utf8") +
                             username.encode("utf8")).hexdigest()
                self.pgexecute('ALTER ROLE "{0}" WITH '
                               'PASSWORD \'md5{1}\''.format(username, pghash))
            if superuser:
                self.pgexecute('ALTER USER "{0}" WITH SUPERUSER'
                               .format(username))
            else:
                self.pgexecute('ALTER USER "{0}" WITH NOSUPERUSER'
                               .format(username))

        return self

    def database(self, name, owner=None, state=PRESENT):
        if state == Postgres.REMOVED:
            self.pgexecute('DROP DATABASE IF EXISTS "{0}"'.format(name))
        else:
            # this may produce an SQL error if the database exists
            self.pgexecute('CREATE DATABASE "{0}"'.format(name), nonzero=True)
            if owner:
                self.pgexecute('ALTER DATABASE "{0}" OWNER TO "{1}"'
                               .format(name, owner))
        return self

    # reload/restart?
