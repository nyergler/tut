from __future__ import absolute_import
import os
import subprocess

import six
from docutils import nodes
from docutils.parsers.rst import Directive, directives
import sphinx.pycode
from sphinx.directives.code import dedent_lines

from .manager import TutManager


class TutExec(Directive):

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        'path': directives.path,
        'hide-output': directives.flag,
        'hide-commands': directives.flag,
        'prelude': directives.unchanged,
    }
    # TK: include_commands, include_output, final_prompt, prelude

    def run(self):
        manager = TutManager.get(self.state.document.settings.env)
        root = self.options.get('path', manager.default_path)
        rel_path, root = self.state.document.settings.env.relfn2path(root)

        show_commands = 'hide-commands' not in self.options
        show_output = 'hide-output' not in self.options

        output = []
        lines = self.content

        for line in lines:
            cmd = subprocess.run(
                line.strip().split('$ ', 1)[-1],
                cwd=root, shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding='utf8',
                universal_newlines=True,
            )
            if show_commands:
                output.append(line)
            # TK: check stderr
            cmd_output = cmd.stdout.strip()
            if show_output and cmd_output:
                output.append(cmd_output)

        code = '\n'.join(output)
        return [
            nodes.literal_block(code, code),
        ]


class TutContent(Directive):

    has_content = True
    required_arguments = 1
    optional_arguments = 0

    def run(self):
        manager = TutManager.get(self.state.document.settings.env)
        root = self.options.get('path', manager.default_path)
        path = os.path.join(root, self.arguments[0])
        rel_path, path = self.state.document.settings.env.relfn2path(path)

        content = '\n'.join(self.content)
        open(path, 'w').write(content)

        # TK: Highlighting as in code blocks
        return [
            nodes.literal_block(content, content),
        ]
