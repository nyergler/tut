from __future__ import absolute_import
import os

import six
import sh
from sh import git
from docutils.parsers.rst import Directive, directives
import sphinx.pycode


_DEFAULT_PATH = None
_RESET_PATHS = {}


class TutDefaults(Directive):
    option_spec = {
        'path': directives.path,
    }

    def run(self):

        global _DEFAULT_PATH
        _DEFAULT_PATH = self.options['path']

        return []


class TutCheckpoint(Directive):

    has_content = False
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        'path': directives.path,
    }

    def run(self):

        global _DEFAULT_PATH
        global _RESET_PATHS

        if 'path' in self.options:
            tut_path = self.options['path']
        elif _DEFAULT_PATH is not None:
            tut_path = _DEFAULT_PATH
        else:
            raise Exception("No tut path specified.")

        # paths are relative to the project root
        rel_path, tut_path = self.state.document.settings.env.relfn2path(
            tut_path)

        curdir = os.getcwd()
        os.chdir(tut_path)

        # if this is the first time visiting this repo
        if tut_path not in _RESET_PATHS:
            # record the current branch
            _RESET_PATHS[tut_path] = \
                git('name-rev', 'HEAD').strip().split()[-1]

        git_ref = self.arguments[0].strip().lower()
        try:
            git.checkout(git_ref)

        except sh.ErrorReturnCode_1 as git_error:
            if six.b(
                "error: pathspec '%s' did not match any "
                "file(s) known to git.\n" % (
                    git_ref,
                )
            ) == git_error.stderr:
                raise ValueError(
                    "git checkpoint '%s' does not exist." % (git_ref,)
                )

        finally:
            sphinx.pycode.ModuleAnalyzer.cache = {}

        os.chdir(curdir)

        return []


def initialize(app):

    global _RESET_PATHS
    _RESET_PATHS = {}


def cleanup(app, exception):

    global _RESET_PATHS

    curdir = os.getcwd()
    try:
        for path in _RESET_PATHS:
            os.chdir(path)
            git.checkout(_RESET_PATHS[path])
    finally:
        os.chdir(curdir)


def setup(app):

    app.add_directive('tut', TutDefaults)
    app.add_directive('checkpoint', TutCheckpoint)

    app.connect('builder-inited', initialize)
    app.connect('build-finished', cleanup)
