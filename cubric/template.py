import plumbum
import tempfile
import inspect

from path import Path

from jinja2 import Template as J2Template, TemplateSyntaxError
from .cubric import Tool, TemplateException, NotFoundException


class Template(Tool):

    def create(self, src, dst, args, **kwargs):
        # fullargs = args.copy()
        # fullargs['cubric'] = 'managed by Cubric'

        caller = inspect.stack()[1]
        callerbase = Path(caller.filename).dirname()

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
        # TODO: check md5sums, if changed (or missing), copy file

        with tempfile.NamedTemporaryFile() as fp:
            fp.write(rendered.encode('utf8'))
            fp.flush()

            plumbum.path.utils.copy(fp.name, self.env.host.path(dst))
        return self
