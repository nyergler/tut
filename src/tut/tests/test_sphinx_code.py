import os.path
from unittest import TestCase
from unittest.mock import patch

from sphinx_testing import with_app
from sphinx_testing.path import path

from tut.sphinx.manager import TutManager


test_root = path(__file__).parent.joinpath('root').abspath().parent


@patch('tut.sphinx.code.TutManager.get')
class TutLiteralIncludeTests(TestCase):

    @with_app(srcdir=test_root/'literalinclude')
    def test_literalinclude_fetches_from_git(self, git_mock, sphinx_app, status, warning):

        git_mock().configure_mock(**{
            'resolve_option.return_value': '/testing',
        })
        git_mock().tut().configure_mock(**{
            'file.return_value': b'foobar',
            'path': test_root/'literalinclude'/'testing',
        })
        sphinx_app.builder.build_all()

        self.assertEqual(git_mock().tut().file.call_count, 1)
        self.assertEqual(
            git_mock().tut().file.call_args[0],
            ('step_one', 'setup.py'),
        )

        # ensure the content was correctly included
        with open(os.path.join(sphinx_app.builddir, 'html', 'index.html')) as output_html:
            self.assertIn('foobar', output_html.read())
