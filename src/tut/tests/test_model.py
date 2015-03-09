import os
import shutil
import tempfile
import unittest

from mock import patch
from sh import git

import tut.model


class TutPointTests(unittest.TestCase):

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

    def test_init_creates_empty_pointfile(self):

        t = tut.model.Tut(self._testpath)
        t.init()

        os.chdir(self._testpath)
        self.assertEqual(
            git('--no-pager', 'show', 'tut:tut.cfg').strip(),
            'points: []',
        )

    def test_points_returns_contents_of_pointfile(self):
        t = tut.model.Tut(self._testpath)
        t.init()

        self.assertEqual(t.points(), [])

        t.start('step1')
        t.start('step2')

        self.assertEqual(t.points(), ['step1', 'step2'])

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
        self.assertEqual(True, False)

    def test_start_inserts_branch_after_last(self):
        pass
