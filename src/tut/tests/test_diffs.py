import textwrap
import unittest

from tut import diff


class DiffTests(unittest.TestCase):

    def test_equal_objects_return_empty_string(self):

        self.assertEqual(diff.diff_contents('A', 'A'), '')

    def test_adding_new_toplevel_returns_lines(self):

        previous = textwrap.dedent(
            """
            import sys
            import os
            """,
        )
        now = textwrap.dedent(
            """
            import sys
            import os
            import unittest
            """,
        )

        self.assertEqual(
            diff.diff_contents(previous, now),
            'import unittest\n',
        )

    def test_adding_lines_in_func_returns_new_func(self):
        previous = textwrap.dedent(
            """
            import sys

            def foo():
                pass
            """,
        )
        now = textwrap.dedent(
            """
            import sys

            def foo():
                return 42
            """,
        )

        self.assertEqual(
            diff.diff_contents(previous, now),
            textwrap.dedent(
            """\
            def foo():
                return 42
            """)
        )

    def test_removing_lines_in_func_returns_new_func(self):
        previous = textwrap.dedent(
            """
            import sys

            def foo():
                a = 42
                return a
            """,
        )
        now = textwrap.dedent(
            """
            import sys

            def foo():
                return 42
            """,
        )

        self.assertEqual(
            diff.diff_contents(previous, now),
            textwrap.dedent(
            """\
            def foo():
                return 42
            """)
        )

    def test_ellipsis_between_changes(self):
        previous = textwrap.dedent(
            """
            import sys

            def foo():
                a = 42
                return a
            """,
        )
        now = textwrap.dedent(
            """
            import os
            import sys

            def foo():
                return os.getcwd()
            """,
        )

        self.assertEqual(
            diff.diff_contents(previous, now),
            textwrap.dedent(
            """\
            import os

            ...

            def foo():
                return os.getcwd()
            """)
        )

    def test_add_method_includes_class_header(self):
        self.assertEqual(
            diff.diff_contents(TEST_CLASS, TEST_CLASS_2, name='adder.py'),
            textwrap.dedent("""\
            class Adder(object):

            ...

                def result(self):
                    return sum(self._args)
            """),
        )

    def test_change_method_includes_class_header(self):
        self.assertEqual(
            diff.diff_contents(TEST_CLASS_3, TEST_CLASS_2, name='adder.py'),
            textwrap.dedent("""\
            class Adder(object):

            ...

                def result(self):
                    return sum(self._args)
            """),
        )

    def test_top_level_constant_diff(self):
        self.assertEqual(
            diff.diff_contents(SETTINGS_1, SETTINGS_2, name='settings.py'),
            textwrap.dedent("""\
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': os.path.join(BASE_DIR, 'addresses.sqlite3'),
                }
            }
            """),
        )


TEST_CLASS = """

class Adder(object):

    def __init__(self, *args):
        self._args = args
"""

TEST_CLASS_2 = """

class Adder(object):

    def __init__(self, *args):
        self._args = args

    def result(self):
        return sum(self._args)

"""

TEST_CLASS_3 = """

class Adder(object):

    def __init__(self, *args):
        self._args = args

    def result(self):
        return self._args[0] + self._args[1]

"""

SETTINGS_1 = """
WSGI_APPLICATION = 'addressbook.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
"""

SETTINGS_2 = """
WSGI_APPLICATION = 'addressbook.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'addresses.sqlite3'),
    }
}
"""
