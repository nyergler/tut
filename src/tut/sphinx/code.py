import codecs
import logging

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.directives.code import (
    container_wrapper,
    dedent_lines,
    LiteralInclude,
)
from sphinx.util import parselinenos
from sphinx.util.nodes import set_source_info

from tut import diff
from .manager import TutManager


class TutLiteralInclude(LiteralInclude):

    def read_with_encoding(self, filename, document, codec_info, encoding):
        # get the current Tut
        manager = TutManager.get(self.state.document.settings.env)

        if 'path' in self.options:
            tut_path = self.options['path']
        elif manager.default_path is not None:
            tut_path = manager.default_path
        else:
            raise Exception("No tut path specified.")
        rel_path, tut_path = self.state.document.settings.env.relfn2path(
            tut_path)

        rel_fn, _ = self.state.document.settings.env.relfn2path(self.arguments[0])

        tut = manager.tut(tut_path)
        try:
            text = tut.file(self.state.document.git_ref, rel_fn[len(rel_path) + 1:]).decode('utf-8')
            if 'tab-width' in self.options:
                text = text.expandtabs(self.options['tab-width'])

            lines = text.splitlines(True)
            if 'dedent' in self.options:
                return dedent_lines(lines, self.options.get('dedent'), location=location)
            else:
                return lines
        except (IOError, OSError):
            raise IOError(_('Include file %r not found or reading it failed') % filename)
        except UnicodeError:
            raise UnicodeError(_('Encoding %r used for reading included file %r seems to '
                                 'be wrong, try giving an :encoding: option') %
                               (self.encoding, filename))


class TutCodeDiff(Directive):
    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'path': directives.path,
        'prev_ref': directives.unchanged,
        'ref': directives.unchanged,
    }

    def run(self):
        manager = TutManager.get(self.state.document.settings.env)

        if 'path' in self.options:
            tut_path = self.options['path']
        elif manager.default_path is not None:
            tut_path = manager.default_path
        else:
            raise Exception("No tut path specified.")

        # paths are relative to the project root
        rel_path, tut_path = self.state.document.settings.env.relfn2path(
            tut_path)
        rel_obj_name, _ = self.state.document.settings.env.relfn2path(
            self.arguments[0],
        )
        rel_obj_name = rel_obj_name[len(rel_path) + 1:]

        # use the last checkpoint set if ref is not specified
        ref = self.options.get('ref', self.state.document.git_ref)

        # use the previous point if prev_ref is not specified
        prev_ref = self.options.get('prev_ref')
        if not prev_ref:
            points = manager.tut(tut_path).points()
            prev_ref = points[points.index(ref) - 1]

        new = manager.tut(tut_path).file(ref, rel_obj_name).decode('utf8')
        old = manager.tut(tut_path).file(prev_ref, rel_obj_name).decode('utf8')

        code = diff.diff_contents(old, new, name=rel_obj_name)
        literal = nodes.literal_block(code, code)
        ## literal['language'] = self.arguments[0]

        return [literal]
