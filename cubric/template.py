import plumbum
import tempfile

from path import Path

from jinja2 import Template as J2Template, TemplateSyntaxError
from .cubric import Tool


class Template(Tool):

    def create(self, src, dst, args):
        # fullargs = args.copy()
        # fullargs['cubric'] = 'managed by Cubric'

        try:
            dir = Path(__file__).dirname()
            data = open(dir / src, "r").read()
        except FileNotFoundError:
            data = open(src, "r").read()

        try:
            template = J2Template(data)
        except TemplateSyntaxError as e:
            raise TemplateException(
                "{src}:{line} => {message}".format(src=src, message=e.message,
                                                   line=e.lineno)) from None

        vars = args.dict()
        vars['ENV'] = [{"key": k, "value": v}
                       for (k, v) in self.env.env.items()]

        rendered = template.render(vars)
        # TODO: check md5sums, if changed (or missing), copy file

        with tempfile.NamedTemporaryFile() as fp:
            fp.write(rendered.encode('utf8'))
            fp.flush()

            plumbum.path.utils.copy(fp.name, self.env.host.path(dst))
        return self
