import functools
import os

from sh import git
import yaml


DEFAULT_CONFIG = {
    'points': [],
}


class TutException(Exception):
    pass


class Tut(object):

    def __init__(self, path):
        self.path = path

        # record the current branch
        self._initial_rev = None
        try:
            self._initial_rev = self._current_branch()
        except Exception as e:
            pass

    def _git(self, *args, **kwargs):

        return git(
            '--git-dir={0}'.format(os.path.join(self.path, '.git')),
            '--work-tree={0}'.format(self.path),
            *args, **kwargs
        )

    def _repo_dirty(self):
        """Return True if the repository is dirty."""

        UNCHANGED_STATUSES = (' ', '?', '!')

        for status_line in self._git('status', porcelain=True):
            if not(status_line[0] in UNCHANGED_STATUSES and
                   status_line[1] in UNCHANGED_STATUSES):
                return True

        return False

    def _config(self):
        return yaml.load(self.file('tut', 'tut.cfg'))

    def _update_config(self, config, log=None):

        branch = self._current_branch()

        try:
            self._git('checkout', 'tut')
            yaml.dump(
                config,
                open(os.path.join(self.path, 'tut.cfg'), 'w'),
                default_flow_style=False,
            )
            self._git('add', 'tut.cfg')
            self._git('commit',
                m=log or 'Update configuration.',
            )

        finally:
            self._git('checkout', branch)

    def init(self):
        """Create a new repository with an initial commit."""

        cwd = os.getcwd()

        # initialize the empty repository
        git.init(self.path)

        self._git('commit',
            m='Initializing empty Tut project.',
            allow_empty=True,
        )

        # create the empty configuration file
        self._git('branch', 'tut')
        self._update_config(
            DEFAULT_CONFIG,
            log='Initializing Tut configuration.',
        )
        self._git('checkout', 'master')

    def file(self, branch, path):
        return self._git('--no-pager', 'show', f'{branch}:{path}').stdout

    def points(self, remote=None):
        """Return a list of existing checkpoints (branches).

        The list is returned with the oldest checkpoint first.

        """

        return self._config()['points']

    def _current_branch(self):
        """Return the current branch of the repo."""

        return self._git('rev-parse', '--abbrev-ref', 'HEAD').strip()

    def current(self):
        """Return the name of the current step."""

        current_branch = self._current_branch()

        if current_branch in self.points():
            return current_branch

        return None

    def start(self, name, starting_point=None):
        """Start a new step (branch)."""

        # make sure this is not a known checkpoint
        if name in self.points():
            raise TutException("Duplicate checkpoint.")

        # make sure the repo is clean
        if self._repo_dirty():
            raise TutException("Dirty tree.")

        # create the new branch
        self._git('branch', name)

        # add the branch to config
        config = self._config()
        points = config['points']
        if self.current():
            points.insert(points.index(self.current()) + 1, name)
        else:
            points.append(name)

        self._update_config(
            config,
            log='Adding new point %s' % name,
        )

        # checkout the new branch
        self._git('checkout', name)

    def checkout(self, ref):
        self._git('checkout', ref)

    def edit(self, name):
        """Start editing the checkpoint point_name."""

        # make sure this is a known checkpoint
        if name not in self.points():
            raise TutException("Unknown checkpoint.")

        # make sure the repo is clean
        if self._repo_dirty():
            raise TutException("Dirty tree.")

        self.checkout(name)

    def next(self, merge=False):
        current = self.current()

        try:
            switch_to = self.points()[
                self.points().index(current) + 1
            ]
        except IndexError:
            # we've reached the end of the list; switch to master
            switch_to = 'master'

        self._git('checkout', switch_to)

        if merge:
            self._git('merge', current)

    def reset(self):
        """Reset the repo to the rev it was at when we started."""

        if self._initial_rev is not None:
            self.checkout(self._initial_rev)
