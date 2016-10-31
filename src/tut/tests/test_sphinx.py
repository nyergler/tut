import os
from os import chdir as _chdir
from unittest import TestCase

from mock import patch

from tut.sphinx.manager import TutManager
import tut.sphinx.checkpoint

from tut.tests import util
from tut.tests.util import with_sphinx


@patch('os.chdir', new=lambda x: _chdir(x) if os.path.exists(x) else None)
@patch('tut.sphinx.checkpoint.git', return_value='original_branch')
class SphinxExtensionLifecycleTests(TestCase):

    # the order of these decorators is *important*: cleanup needs to
    # be replaced before the Sphinx Test Application is instantiated
    @patch('tut.sphinx.cleanup')
    @with_sphinx()
    def test_cleanup_called(self, cleanup_mock, git_mock, sphinx_app=None):

        sphinx_app.build(force_all=True)

        self.assertEqual(cleanup_mock.call_count, 1)

    @with_sphinx()
    def test_cleanup_resets_paths(self, git_mock, sphinx_app=None):

        start_dir = os.getcwd()

        sphinx_app.build()

        self.assertEqual(git_mock.checkout.call_count, 2)
        self.assertEqual(git_mock.checkout.call_args_list[0][0],
                         ('step_one',))
        self.assertEqual(git_mock.checkout.call_args_list[1][0],
                         ('original_branch',))

        self.assertEqual(start_dir, os.getcwd())


@patch('os.chdir', new=lambda x: _chdir(x) if os.path.exists(x) else None)
@patch('tut.sphinx.checkpoint.git', return_value='x')
class TutDirectiveTests(TestCase):

    @with_sphinx(srcdir=util.test_root.parent/'tut_directive')
    def test_set_default_path(self, git_mock, sphinx_app=None):
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


@patch('os.chdir', new=lambda x: _chdir(x) if os.path.exists(x) else None)
@patch('tut.sphinx.checkpoint.git', return_value='x')
class CheckpointDirectiveTests(TestCase):

    @with_sphinx()
    def test_checkpoint_triggers_checkout(self, git_mock, sphinx_app=None):
        sphinx_app.build()

        self.assertEqual(git_mock.checkout.call_count, 2)
        self.assertEqual(git_mock.checkout.call_args_list[0][0],
                         ('step_one',))

    @with_sphinx()
    def test_checkpoint_resets_pycode_cache(self, git_mock, sphinx_app=None):

        # dirty the cache
        import sphinx.pycode
        sphinx.pycode.ModuleAnalyzer.cache = {'foo': 'bar'}

        # build the project, which includes a checkout directive
        sphinx_app.build()

        self.assertEqual(sphinx.pycode.ModuleAnalyzer.cache, {})

    @with_sphinx(srcdir=util.test_root.parent/'relative_path')
    def test_relative_paths(self, git_mock, sphinx_app=None):
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

    @with_sphinx(srcdir=util.test_root.parent/'abs_path')
    def test_absolute_paths(self, git_mock, sphinx_app=None):
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


@patch('os.chdir', new=lambda x: _chdir(x) if os.path.exists(x) else None)
class CheckpointDirectiveWithLiveGitTests(TestCase):

    @with_sphinx(srcdir=util.test_root.parent/'abs_path')
    def test_invalid_checkpoint(self, sphinx_app=None):
        """Invalid checkpoint names return helpful error message."""

        with self.assertRaises(ValueError) as git_error:
            sphinx_app.builder.build_all()

        self.assertEqual(
            str(git_error.exception),
            "git checkpoint 'step_one' does not exist.",
        )

        # cleanup
        sphinx_app.cleanup()
        sphinx_app.builder.cleanup()
