from __future__ import absolute_import
import os

import six
import sh
from sh import git
from docutils.parsers.rst import Directive, directives
import sphinx.pycode

from .manager import TutManager


class TutDefaults(Directive):
    option_spec = {
        'path': directives.path,
    }

    def run(self):
        manager = TutManager.get(self.state.document.settings.env)

        manager.default_path = self.options['path']

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

        curdir = os.getcwd()
        os.chdir(tut_path)

        # if this is the first time visiting this repo
        if tut_path not in manager.reset_paths:
            # record the current branch
            manager.reset_paths[tut_path] = \
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

    TutManager.get(app.env).reset()


def cleanup(app, exception):

    manager = TutManager.get(app.env)

    curdir = os.getcwd()
    try:
        for path in manager.reset_paths:
            os.chdir(path)
            git.checkout(manager.reset_paths[path])
    finally:
        os.chdir(curdir)
