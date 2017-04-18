import os
from unittest import TestCase

from mock import (
    ANY,
    patch,
)
from munch import munchify
from sphinx_testing import with_app
from sphinx_testing.path import path

from tut.sphinx.manager import TutManager
import tut.sphinx.checkpoint


test_root = path(__file__).parent.joinpath('root').abspath()


@patch('tut.model.git', return_value='original_branch')
class SphinxExtensionLifecycleTests(TestCase):

    # the order of these decorators is *important*: cleanup needs to
    # be replaced before the Sphinx Test Application is instantiated
    @patch('tut.sphinx.cleanup')
    @with_app(srcdir=test_root)
    def test_cleanup_called(self, cleanup_mock, git_mock, sphinx_app, status, warning):

        sphinx_app.build(force_all=True)

        self.assertEqual(cleanup_mock.call_count, 1)

    @with_app(srcdir=test_root)
    def test_cleanup_resets_paths(self, git_mock, sphinx_app, status, warning):

        start_dir = os.getcwd()

        sphinx_app.build()

        self.assertEqual(git_mock.call_count, 3)
        self.assertEqual(git_mock.call_args_list[1][0],
                         (ANY, ANY, 'checkout', 'step_one',))
        self.assertEqual(git_mock.call_args_list[2][0],
                         (ANY, ANY, 'checkout', 'original_branch',))

        self.assertEqual(start_dir, os.getcwd())


@patch('tut.model.git', return_value='x')
class TutDirectiveTests(TestCase):

    @with_app(srcdir=test_root.parent/'tut_directive')
    def test_set_default_path(self, git_mock, sphinx_app, status, warning):
        """tut directive sets the default repo path."""

        sphinx_app.builder.build_all()

        # check the resolved paths in the cache
        self.assert_(
            os.path.join(
                os.path.dirname(__file__), 'tut_directive', 'src'
            ) in TutManager.get(sphinx_app.env).reset_paths
        )
        self.assertEqual(TutManager.get(sphinx_app.env).default_path, '/src')

        # cleanup
        sphinx_app.cleanup()
        sphinx_app.builder.cleanup()


@patch('tut.model.git', return_value='x')
class CheckpointDirectiveTests(TestCase):

    @with_app(srcdir=test_root)
    def test_checkpoint_triggers_checkout(self, git_mock, sphinx_app, status, warning):
        sphinx_app.build()

        self.assertEqual(git_mock.call_count, 3)
        self.assertEqual(git_mock.call_args_list[1][0],
                         (ANY, ANY, 'checkout', 'step_one',))

    @with_app(srcdir=test_root)
    def test_checkpoint_resets_pycode_cache(self, git_mock, sphinx_app, status, warning):

        # dirty the cache
        import sphinx.pycode
        sphinx.pycode.ModuleAnalyzer.cache = {'foo': 'bar'}

        # build the project, which includes a checkout directive
        sphinx_app.build()

        self.assertEqual(sphinx.pycode.ModuleAnalyzer.cache, {})

    @with_app(srcdir=test_root.parent/'relative_path')
    def test_relative_paths(self, git_mock, sphinx_app, status, warning):
        """Paths are relative to the document location."""

        sphinx_app.builder.build_all()

        # check the resolved paths in the cache
        self.assert_(
            os.path.join(
                os.path.dirname(__file__), 'relative_path', 'src'
            ) in TutManager.get(sphinx_app.env).reset_paths
        )

        # cleanup
        sphinx_app.cleanup()
        sphinx_app.builder.cleanup()

    @with_app(srcdir=test_root.parent/'abs_path')
    def test_absolute_paths(self, git_mock, sphinx_app, status, warning):
        """Absolute paths are relative to the project root."""

        sphinx_app.builder.build_all()

        # check the resolved paths in the cache
        self.assert_(
            os.path.join(
                os.path.dirname(__file__), 'abs_path', 'src'
            ) in TutManager.get(sphinx_app.env).reset_paths
        )

        # cleanup
        sphinx_app.cleanup()
        sphinx_app.builder.cleanup()


class CheckpointDirectiveWithLiveGitTests(TestCase):

    def test_invalid_checkpoint(self):
        """Invalid checkpoint names return helpful error message."""

        node = tut.sphinx.checkpoint.TutCheckpoint(
            'checkpoint',
            ('blarf',),
            {'path': os.getcwd()},
            content='',
            lineno=0,
            content_offset=0,
            block_text=None,
            state=munchify({
                'document': {
                    'settings': {
                        'env': {
                            'relfn2path': lambda p: (p, p)
                        },
                    },
                },
            }),
            state_machine=None,
        )

        with self.assertRaises(ValueError) as git_error:
            node.run()

        self.assertEqual(
            str(git_error.exception),
            "git checkpoint 'blarf' does not exist.",
        )
