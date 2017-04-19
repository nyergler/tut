import difflib

import re

from sphinx.pycode import ModuleAnalyzer as SphinxModuleAnalyzer
from sphinx.pycode.pgen2 import token


emptyline_re = re.compile(r'^\s*(#.*)?$')


# Extend Sphinx's Module Analyzer to support top-leve constants
class ModuleAnalyzer(SphinxModuleAnalyzer):

    def find_tags(self):
        """Find class, function and method definitions and their location."""
        if self.tags is not None:
            return self.tags
        self.tokenize()
        result = {}
        namespace = []  # type: List[unicode]
        stack = []      # type: List[Tuple[unicode, unicode, unicode, int]]
        indent = 0
        decopos = None
        defline = False
        expect_indent = False
        emptylines = 0

        def tokeniter(ignore = (token.COMMENT,)):
            for tokentup in self.tokens:
                if tokentup[0] not in ignore:
                    yield tokentup
        tokeniter = tokeniter()
        for type, tok, spos, epos, line in tokeniter:  # type: ignore
            if expect_indent and type != token.NL:
                if type != token.INDENT:
                    # no suite -- one-line definition
                    assert stack
                    dtype, fullname, startline, _ = stack.pop()
                    endline = epos[0]
                    namespace.pop()
                    result[fullname] = (dtype, startline, endline - emptylines)
                expect_indent = False
            if tok in ('def', 'class'):
                name = next(tokeniter)[1]  # type: ignore
                namespace.append(name)
                fullname = '.'.join(namespace)
                stack.append((tok, fullname, decopos or spos[0], indent))
                defline = True
                decopos = None
            elif type == token.NAME and spos[1] == 0:
                name = fullname = tok
                namespace.append(name)
                stack.append((tok, fullname, decopos or spos[0], indent))
                defline = True
                decopos = None
            elif type == token.OP and tok == '@':
                if decopos is None:
                    decopos = spos[0]
            elif type == token.INDENT:
                expect_indent = False
                indent += 1
            elif type == token.DEDENT:
                indent -= 1
                # if the stacklevel is the same as it was before the last
                # def/class block, this dedent closes that block
                if stack and indent == stack[-1][3]:
                    dtype, fullname, startline, _ = stack.pop()
                    endline = spos[0]
                    namespace.pop()
                    result[fullname] = (dtype, startline, endline - emptylines)
            elif type == token.NEWLINE:
                # if this line contained a definition, expect an INDENT
                # to start the suite; if there is no such INDENT
                # it's a one-line definition
                if defline:
                    defline = False
                    expect_indent = True
                emptylines = 0
            elif type == token.NL:
                # count up if line is empty or comment only
                if emptyline_re.match(line):
                    emptylines += 1
                else:
                    emptylines = 0
        self.tags = result
        return result


def _find_object(codetext, pos_range, name):
    """Find the Python object at pos_range needed for diff context.

    codetext is an array of lines
    pos_range is a two-tuple: (start, end)
    name is a string which may be used to identify the object

    """
    lineno = pos_range[0]

    code = ModuleAnalyzer.for_string(''.join(codetext), name)
    tags = code.find_tags()

    # order the tags by starting position and covert to 0 based indices
    ordered_tags = sorted(
        [[item_type, name, start - 1, end - 1]
         for (name, (item_type, start, end)) in tags.items()],
        key=lambda t: t[2],
    )

    if not ordered_tags:
        return

    # determine the "display end" of each tag
    for i in range(len(ordered_tags) - 1):
        ordered_tags[i].append(ordered_tags[i+1][2])
    ordered_tags[-1].append(ordered_tags[-1][-1])

    # find all overlapping segments
    segments = [
        (item_type, name, start, end, display_end)
        for (item_type, name, start, end, display_end) in ordered_tags
        if (lineno >= start and lineno < end)
    ]

    # generate (start, end) pairs
    for _, _, start, _, end in segments:
        yield start, end


def _strip_lines(lines):

    if not lines:
        return lines

    start = 0
    end = len(lines)

    while not(lines[start].strip()) and start < end:
        start += 1

    while not(lines[end-1].strip()) and end > start:
        end -= 1

    return lines[start:end]


def diff_contents(previously, now, name=''):
    """Given two versions of code and return the diff needed for documentation."""

    previously = previously.splitlines(keepends=True)
    now = now.splitlines(keepends=True)

    result = []
    ranges = []

    for group in difflib.SequenceMatcher(None, previously, now).get_grouped_opcodes(n=0):
        for tag, i1, i2, j1, j2 in group:
            if tag == 'equal':
                ## result.extend(now[j1:j2])
                continue

            if tag in ('insert', 'replace'):
                # determine if this is an indented block or not
                fl_no, first_line = next(
                    (i, line) for (i, line) in enumerate(now[j1:j2], j1)
                    if line.rstrip()
                )

                if first_line[0] != ' ':
                    # this block is unindented, just append it to the result
                    ranges.append((j1, j2))
                else:
                    # grab the object from the code analyzer
                    for start, end in _find_object(now, (fl_no, j2), name=name):
                        ranges.append((start, end))

    # fix up overlapping ranges
    for i in range(len(ranges) - 1):
        # if this range starts before a previous one, fix that
        if i > 0 and ranges[i][0] < ranges[i-1][1]:
            ranges[i] = (ranges[i-1][1], ranges[i][1])

    # fetch the lines and add ellipsis
    ellipsis = ['\n', '...\n', '\n']
    if not ranges:
        return ''

    prev_end = ranges[0][0]
    for start, end in ranges:
        if start > prev_end:
            result.extend(ellipsis)

        result.extend(_strip_lines(now[start:end]))
        prev_end = end

    return ''.join(result)
