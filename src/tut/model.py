import functools
import os

from sh import git
import yaml


DEFAULT_CONFIG = {
    'points': [],
}


def with_path(m):

    @functools.wraps(m)
    def _with_path(self, *args, **kwargs):
        start_path = os.getcwd()
        os.chdir(self.path)
        try:
            return m(self, *args, **kwargs)
        finally:
            os.chdir(start_path)

    return _with_path


class TutException(Exception):
    pass


class Tut(object):

    def __init__(self, path):
        self.path = path

    def _repo_dirty(self):
        """Return True if the repository is dirty."""

        UNCHANGED_STATUSES = (' ', '?', '!')

        for status_line in git.status(porcelain=True):
            if not(status_line[0] in UNCHANGED_STATUSES and
                   status_line[1] in UNCHANGED_STATUSES):
                return True

        return False

    def init(self):
        """Create a new repository with an initial commit."""

        cwd = os.getcwd()

        # initialize the empty repository
        git.init(self.path)

        os.chdir(self.path)
        git.commit(
            m='Initializing empty Tut project.',
            allow_empty=True,
        )

        # create the empty configuration file
        git.checkout('-b', 'tut')
        yaml.dump(
            DEFAULT_CONFIG,
            file('tut.cfg', 'w'),
            default_flow_style=False,
        )
        git.add('tut.cfg')
        git.commit(
            m='Initializing Tut configuration.',
        )
        git.checkout('master')

        os.chdir(cwd)

    def points(self, remote=None):
        """Return a list of existing checkpoints (branches).

        The list is returned with the oldest checkpoint first.

        """

        RESERVED = (
            'HEAD',
        )

        if remote is None:
            prefix = 'refs/heads/'
        else:
            prefix = 'refs/remotes/%s/' % remote

        return [
            step.strip()
            for step in git(
                    'for-each-ref',
                    '--sort=committerdate',
                    prefix,
                    '--format=%(refname:short)',
                )
            if not step.strip().split('/')[-1] in RESERVED
        ]

    def current(self):
        """Return the name of the current step."""

        return git('rev-parse', '--abbrev-ref', 'HEAD').strip()

    @with_path
    def start(self, name, starting_point=None):
        """Start a new step (branch)."""

        # make sure this is not a known checkpoint
        if name in self.points():
            raise TutException("Duplicate checkpoint.")

        # make sure the repo is clean
        if self._repo_dirty():
            raise TutException("Dirty tree.")

        # create the new branch
        git.branch(name)

        if starting_point is None:
            args = ('-b', name)
        else:
            args = ('-b', name, starting_point, '--track')

        # add the branch to config
        git.checkout('tut')
        config = yaml.load(file('tut.cfg', 'r').read())
        config['points'].append(name)
        yaml.dump(config, file('tut.cfg', 'w'), default_flow_style=False)
        git.add('tut.cfg')
        git.commit(m='Adding new point %s' % name)

        # checkout the new branch
        git.checkout(name)

    def edit(self, name):
        """Start editing the checkpoint point_name."""

        # make sure this is a known checkpoint
        if name not in self.points():
            raise TutException("Unknown checkpoint.")

        # make sure the repo is clean
        if self._repo_dirty():
            raise TutException("Dirty tree.")

        git.checkout(name)

    def next(self, merge=False):
        current = self.current()

        try:
            switch_to = self.points()[
                self.points().index(current) + 1
            ]
        except IndexError:
            # we've reached the end of the list; switch to master
            switch_to = 'master'

        git.checkout(switch_to)

        if merge:
            git.merge(current)
