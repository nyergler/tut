import os

from sh import git
from docutils.parsers.rst import Directive, directives


_DEFAULT_PATH = None


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

        if 'path' in self.options:
            tut_path = self.options['path']
        elif _DEFAULT_PATH is not None:
            tut_path = _DEFAULT_PATH
        else:
            raise Exception("No tut path specified.")

        curdir = os.getcwd()
        tut_path = os.path.join(curdir, tut_path)
        os.chdir(tut_path)

        git.checkout(self.arguments[0].strip().lower())

        os.chdir(curdir)

        return []


def setup(app):

    app.add_directive('tut', TutDefaults)
    app.add_directive('checkpoint', TutCheckpoint)
