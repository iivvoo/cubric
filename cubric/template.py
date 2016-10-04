import plumbum
import tempfile
import inspect
import hashlib

from path import Path

from jinja2 import Template as J2Template, TemplateSyntaxError
from .cubric import Tool, TemplateException, NotFoundException, NonZero


class Template(Tool):

    def create(self, src, dst, args, sudo=False, **kwargs):
        # fullargs = args.copy()
        # fullargs['cubric'] = 'managed by Cubric'

        caller = inspect.stack()[1]
        filename = caller[1]  # caller.filename is a 3.5ism
        callerbase = Path(filename).dirname()

        tries = (callerbase / src, Path(__file__).dirname() / src, src)

        for t in tries:
            try:
                data = open(t, "r").read()
                break
            except FileNotFoundError:
                pass
        else:
            raise NotFoundException("Could not find/resolve {0} to a template"
                                    .format(src))
        try:
            template = J2Template(data)
        except TemplateSyntaxError as e:
            raise TemplateException(
                "{src}:{line} => {message}".format(src=src, message=e.message,
                                                   line=e.lineno)) from None

        vars = args.dict()
        vars['ENV'] = [{"key": k, "value": v}
                       for (k, v) in self.env.env.items()]

        vars.update(kwargs)

        rendered = template.render(vars)

        m = hashlib.md5()
        m.update(rendered.encode('utf8'))
        md5sum = m.hexdigest()

        changed = True
        try:
            res = self.env.command("md5sum", dst)
            remotesum = res.split()[0]
            changed = (remotesum != md5sum)
        except NonZero:
            changed = True

        if changed:
            tmpname = "/tmp/{0}".format(next(tempfile._get_candidate_names()))
            with tempfile.NamedTemporaryFile() as fp:
                fp.write(rendered.encode('utf8'))
                fp.flush()

                if sudo:
                    plumbum.path.utils.copy(
                        fp.name, self.env.host.path(tmpname))
                    with self.env.sudo():
                        self.env.command("mv", tmpname, dst)

                else:
                    plumbum.path.utils.copy(fp.name, self.env.host.path(dst))
        self.env.last_result = changed
        return self
