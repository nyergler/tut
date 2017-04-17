import difflib

import re

from six import BytesIO, StringIO

from sphinx.errors import PycodeError
from sphinx.pycode.pgen2 import token, tokenize, parse
from sphinx.util import get_module_source, detect_encoding
from sphinx.util.pycompat import TextIOWrapper


emptyline_re = re.compile(r'^\s*(#.*)?$')


# ModuleAnalyzer borrowed from Sphinx core to add top-level constant support
class ModuleAnalyzer(object):
    # cache for analyzer objects -- caches both by module and file name
    cache = {}  # type: Dict[Tuple[unicode, unicode], Any]

    @classmethod
    def for_string(cls, string, modname, srcname='<string>'):
        if isinstance(string, bytes):
            return cls(BytesIO(string), modname, srcname)
        return cls(StringIO(string), modname, srcname, decoded=True)

    @classmethod
    def for_file(cls, filename, modname):
        if ('file', filename) in cls.cache:
            return cls.cache['file', filename]
        try:
            fileobj = open(filename, 'rb')
        except Exception as err:
            raise PycodeError('error opening %r' % filename, err)
        obj = cls(fileobj, modname, filename)
        cls.cache['file', filename] = obj
        return obj

    @classmethod
    def for_module(cls, modname):
        if ('module', modname) in cls.cache:
            entry = cls.cache['module', modname]
            if isinstance(entry, PycodeError):
                raise entry
            return entry

        try:
            type, source = get_module_source(modname)
            if type == 'string':
                obj = cls.for_string(source, modname)
            else:
                obj = cls.for_file(source, modname)
        except PycodeError as err:
            cls.cache['module', modname] = err
            raise
        cls.cache['module', modname] = obj
        return obj

    def __init__(self, source, modname, srcname, decoded=False):
        # name of the module
        self.modname = modname
        # name of the source file
        self.srcname = srcname
        # file-like object yielding source lines
        self.source = source

        # cache the source code as well
        pos = self.source.tell()
        if not decoded:
            self.encoding = detect_encoding(self.source.readline)
            self.source.seek(pos)
            self.code = self.source.read().decode(self.encoding)
            self.source.seek(pos)
            self.source = TextIOWrapper(self.source, self.encoding)
        else:
            self.encoding = None
            self.code = self.source.read()
            self.source.seek(pos)

        # will be filled by tokenize()
        self.tokens = None      # type: List[unicode]
        # will be filled by parse()
        self.parsetree = None   # type: Any
        # will be filled by find_attr_docs()
        self.attr_docs = None   # type: List[unicode]
        self.tagorder = None    # type: Dict[unicode, int]
        # will be filled by find_tags()
        self.tags = None        # type: List[unicode]

    def tokenize(self):
        """Generate tokens from the source."""
        if self.tokens is not None:
            return
        try:
            self.tokens = list(tokenize.generate_tokens(self.source.readline))
        except tokenize.TokenError as err:
            raise PycodeError('tokenizing failed', err)
        self.source.close()

    def parse(self):
        """Parse the generated source tokens."""
        if self.parsetree is not None:
            return
        self.tokenize()
        try:
            self.parsetree = pydriver.parse_tokens(self.tokens)
        except parse.ParseError as err:
            raise PycodeError('parsing failed', err)

    def find_attr_docs(self, scope=''):
        """Find class and module-level attributes and their documentation."""
        if self.attr_docs is not None:
            return self.attr_docs
        self.parse()
        attr_visitor = AttrDocVisitor(number2name, scope, self.encoding)
        attr_visitor.visit(self.parsetree)
        self.attr_docs = attr_visitor.collected
        self.tagorder = attr_visitor.tagorder
        # now that we found everything we could in the tree, throw it away
        # (it takes quite a bit of memory for large modules)
        self.parsetree = None
        return attr_visitor.collected

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
    code.find_tags()

    # order the tags by starting position and covert to 0 based indices
    ordered_tags = sorted(
        [[item_type, name, start - 1, end - 1]
         for (name, (item_type, start, end)) in code.tags.items()],
        key=lambda t: t[2],
    )

    if not ordered_tags:
        return

    # determine the "display end" of each tag
    for i in range(len(ordered_tags) - 1):
        ordered_tags[i].append(ordered_tags[i+1][2] - 1)
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


def diff_contents(previously, now, name=''):
    """Given two versions of code and return the diff needed for documentation."""

    previously = previously.splitlines(keepends=True)
    now = now.splitlines(keepends=True)

    last = -1
    result = []
    for group in difflib.SequenceMatcher(None, previously, now).get_grouped_opcodes(n=0):
        for tag, i1, i2, j1, j2 in group:
            if tag == 'equal':
                ## result.extend(now[j1:j2])
                continue

            if tag in ('insert', 'replace'):
                if last > 0 and j1 > last:
                    result.extend(['\n', '...\n', '\n'])

                # determine if this is an indented block or not
                fl_no, first_line = next(
                    (i, line) for (i, line) in enumerate(now[j1:j2], j1)
                    if line.rstrip()
                )

                if first_line[0] != ' ':
                    # this block is unindented, just append it to the result
                    result.extend(now[j1:j2])
                else:
                    # grab the object from the code analyzer
                    first = True
                    for start, end in _find_object(now, (fl_no, j2), name=name):
                        if not first:
                            result.extend(['\n', '...\n', '\n'])

                        result.extend(now[start:end])
                        first = False

                last = j2
                continue

    return ''.join(result)
