import os
import shutil
import tempfile
import unittest

from mock import patch
from sh import git

import tut.model


class TutTestCase(unittest.TestCase):

    def setUp(self):

        # create a temporary directory to work in
        self._testpath = tempfile.mkdtemp()

        # stash the current working directory
        self._original_path = os.getcwd()

    def tearDown(self):

        # cleanup working directory
        shutil.rmtree(self._testpath)

        # return to the original working directory
        os.chdir(self._original_path)


class TutInitTests(TutTestCase):

    def test_init_creates_empty_pointfile(self):

        t = tut.model.Tut(self._testpath)
        t.init()

        os.chdir(self._testpath)
        self.assertEqual(
            git('--no-pager', 'show', 'tut:tut.cfg').strip(),
            'points: []',
        )

    def test_tut_can_reset_to_initial_rev(self):

        # create a repository w/ another branch
        t = tut.model.Tut(self._testpath)
        t.init()
        t.start('blarf')
        t.checkout('master')

        t = tut.model.Tut(self._testpath)
        self.assertEqual(t._current_branch(), 'master')
        t.edit('blarf')
        self.assertEqual(t.current(), 'blarf')
        t.reset()

        self.assertEqual(t._current_branch(), 'master')

    def test_reset_doesnt_fail_when_no_initial_rev(self):
        t = tut.model.Tut(self._testpath)
        t.init()
        t.reset()

        self.assertEqual(t._current_branch(), 'master')


class TutPointsTests(TutTestCase):
    def test_points_returns_contents_of_pointfile(self):
        t = tut.model.Tut(self._testpath)
        t.init()

        self.assertEqual(t.points(), [])

        t.start('step1')
        t.start('step2')

        self.assertEqual(t.points(), ['step1', 'step2'])

    def test_current(self):
        t = tut.model.Tut(self._testpath)
        t.init()

        self.assertEqual(t.current(), None)

        t.start('step1')
        self.assertEqual(t.current(), 'step1')

    def test_current_returns_none_on_unknown_branch(self):
        t = tut.model.Tut(self._testpath)
        t.init()
        t.start('step1')

        t.checkout('master')

        self.assertNotIn('master', t.points())
        self.assertEqual(t.current(), None)


class TutStartEditTests(TutTestCase):

    def test_start_adds_name_to_pointfile(self):
        t = tut.model.Tut(self._testpath)

        t.init()
        t.start('step1')

        os.chdir(self._testpath)
        self.assertEqual(
            git('--no-pager', 'show', 'tut:tut.cfg').strip(),
            'points:\n- step1',
        )

    def test_start_raises_exception_on_duplicate_name(self):
        t = tut.model.Tut(self._testpath)

        t.init()
        t.start('step1')

        with self.assertRaises(tut.model.TutException):
            t.start('step1')

    def test_start_inserts_branch_after_current(self):
        t = tut.model.Tut(self._testpath)
        t.init()

        # create three steps
        t.start('step1')
        t.start('step2')
        t.start('step3')

        t.edit('step2')

        # sanity check
        self.assertEqual(t.current(), 'step2')

        # add new step between 2 and 3
        t.start('step2a')

        self.assertEqual(
            t.points(),
            ['step1',
             'step2',
             'step2a',
             'step3',
            ],
        )

    def test_start_inserts_branch_after_last_on_master(self):
        t = tut.model.Tut(self._testpath)
        t.init()

        # create three steps
        t.start('step1')
        t.start('step2')
        t.start('step3')

        t.checkout('master')

        # add new step at the end
        t.start('step4')

        self.assertEqual(
            t.points(),
            ['step1',
             'step2',
             'step3',
             'step4',
            ],
        )


class TutNextTests(TutTestCase):

    def test_next_checks_out_next_in_list(self):

        t = tut.model.Tut(self._testpath)
        t.init()

        # create three steps
        t.start('step1')
        t.start('step2')
        t.start('step3')

        t.edit('step1')

        self.assertEqual(t._current_branch(), 'step1')

        t.next()
        self.assertEqual(t._current_branch(), 'step2')
        self.assertEqual(t.current(), 'step2')


class TutFileTests(TutTestCase):

    def test_file_retrieves_content_from_branch(self):

        t = tut.model.Tut(self._testpath)
        t.init()

        os.chdir(self._testpath)
        self.assertEqual(
            t.file('tut', 'tut.cfg').strip(),
            b'points: []',
        )
