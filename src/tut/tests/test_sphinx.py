import os
from unittest import TestCase

from mock import patch

import tut.sphinx
from tut.tests import util
from tut.tests.util import with_sphinx


@patch('os.chdir', new=lambda x:None)
@patch('tut.sphinx.git', return_value='original_branch')
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


@patch('os.chdir', new=lambda x:None)
@patch('tut.sphinx.git')
class TutDirectiveTests(TestCase):

    @with_sphinx(srcdir=util.test_root.parent/'tut_directive')
    def test_set_default_path(self, git_mock, sphinx_app=None):
        """tut directive sets the default repo path."""

        self.assertEqual(tut.sphinx._DEFAULT_PATH, None)
        sphinx_app.builder.build_all()

        # check the resolved paths in the cache
        self.assert_(
            os.path.join(
                os.path.dirname(__file__), 'tut_directive', 'src'
            ) in tut.sphinx._RESET_PATHS
        )
        self.assertEqual(tut.sphinx._DEFAULT_PATH, '/src')

        # cleanup
        sphinx_app.cleanup()
        sphinx_app.builder.cleanup()


@patch('os.chdir', new=lambda x:None)
@patch('tut.sphinx.git')
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
            ) in tut.sphinx._RESET_PATHS
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
            ) in tut.sphinx._RESET_PATHS
        )

        # cleanup
        sphinx_app.cleanup()
        sphinx_app.builder.cleanup()
