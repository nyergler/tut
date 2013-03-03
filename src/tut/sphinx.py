from __future__ import absolute_import
import os

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
        if tut_path[0] == '/':
            tut_path = tut_path[1:]

        curdir = os.getcwd()
        tut_path = os.path.join(curdir, tut_path)
        os.chdir(tut_path)

        # if this is the first time visiting this repo
        if tut_path not in _RESET_PATHS:
            # record the current branch
            _RESET_PATHS[tut_path] = \
                git('name-rev', 'HEAD').strip().split()[-1]

        git.checkout(self.arguments[0].strip().lower())
        sphinx.pycode.ModuleAnalyzer.cache = {}

        os.chdir(curdir)

        return []


def cleanup(app, exception):

    global __RESET_PATHS

    for path in _RESET_PATHS:
        os.chdir(path)
        git.checkout(_RESET_PATHS[path])


def setup(app):

    app.add_directive('tut', TutDefaults)
    app.add_directive('checkpoint', TutCheckpoint)

    app.connect('build-finished', cleanup)
