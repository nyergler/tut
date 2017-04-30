from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList
from sphinx.directives.code import (
    dedent_lines,
    LiteralInclude,
    LiteralIncludeReader as SphinxLiteralIncludeReader,
)
from sphinx.util.nodes import set_source_info

from tut import diff
from .manager import TutManager


class LiteralIncludeReader(SphinxLiteralIncludeReader):

    def __init__(self, filename, options, config, tut, gitref):
        self._tut = tut
        self._gitref = gitref

        super().__init__(filename, options, config)

    def read_file(self, filename, location=None):
        # type: (unicode, Any) -> List[unicode]

        try:
            text = self._tut.file(self._gitref, self.filename[len(self._tut.path) + 1:]).decode(self.encoding)

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

class TutLiteralInclude(LiteralInclude):

    def run(self):
        # type: () -> List[nodes.Node]
        document = self.state.document
        if not document.settings.file_insertion_enabled:
            return [document.reporter.warning('File insertion disabled',
                                              line=self.lineno)]
        env = document.settings.env

        # get the current Tut
        manager = TutManager.get(env)
        rel_path, tut_path = self.state.document.settings.env.relfn2path(
            manager.resolve_option(self, 'path'),
        )

        # convert options['diff'] to absolute path
        if 'diff' in self.options:
            _, path = env.relfn2path(self.options['diff'])
            self.options['diff'] = path

        try:
            location = self.state_machine.get_source_and_line(self.lineno)
            rel_filename, filename = env.relfn2path(self.arguments[0])
            env.note_dependency(rel_filename)

            reader = LiteralIncludeReader(
                filename, self.options, env.config,
                tut=manager.tut(tut_path),
                gitref=self.state.document.git_ref,
            )
            text, lines = reader.read(location=location)

            retnode = nodes.literal_block(text, text, source=filename)
            set_source_info(self, retnode)
            if self.options.get('diff'):  # if diff is set, set udiff
                retnode['language'] = 'udiff'
            elif 'language' in self.options:
                retnode['language'] = self.options['language']
            retnode['linenos'] = ('linenos' in self.options or
                                  'lineno-start' in self.options or
                                  'lineno-match' in self.options)
            retnode['classes'] += self.options.get('class', [])
            extra_args = retnode['highlight_args'] = {}
            if 'emphasize-lines' in self.options:
                hl_lines = parselinenos(self.options['emphasize-lines'], lines)
                if any(i >= lines for i in hl_lines):
                    logger.warning('line number spec is out of range(1-%d): %r' %
                                   (lines, self.options['emphasize_lines']),
                                   location=location)
                extra_args['hl_lines'] = [x + 1 for x in hl_lines if x < lines]
            extra_args['linenostart'] = reader.lineno_start

            if 'caption' in self.options:
                caption = self.options['caption'] or self.arguments[0]
                retnode = container_wrapper(self, retnode, caption)

            # retnode will be note_implicit_target that is linked from caption and numref.
            # when options['name'] is provided, it should be primary ID.
            self.add_name(retnode)

            return [retnode]
        except Exception as exc:
            return [document.reporter.warning(str(exc), line=self.lineno)]


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

        tut_path = manager.resolve_option(self, 'path')
        tut_href = manager.resolve_option(self, 'href', None)

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
        literal['language'] = 'python'

        if tut_href:
            link = tut_href.format(checkpoint=ref, path=rel_obj_name)
            caption = 'View file `{0} <{2}>`__'.format(rel_obj_name, ref, link)
            literal = container_wrapper(self, literal, caption)

        return [literal]


def container_wrapper(directive, literal_node, caption):
    container_node = nodes.container('', literal_block=True,
                                     classes=['literal-diff-wrapper'])
    parsed = nodes.Element()
    directive.state.nested_parse(ViewList([caption], source=''),
                                 directive.content_offset, parsed)
    if isinstance(parsed[0], nodes.system_message):
        raise ValueError(parsed[0])
    caption_node = nodes.caption(parsed[0].rawsource, '',
                                 *parsed[0].children)
    caption_node.source = literal_node.source
    caption_node.line = literal_node.line
    container_node += caption_node
    container_node += literal_node
    return container_node
