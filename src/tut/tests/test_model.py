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

        # change to the test repo path
        os.chdir(self._testpath)

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

        git.checkout('master')

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

        git.checkout('master')

        # add new step between 2 and 3
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
