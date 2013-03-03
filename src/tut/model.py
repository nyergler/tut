import os
import sys

from sh import (
    git,
    which,
)


BRANCH_PREFIX = '_tut_edit_'


def branch_name(tag_or_point):

    return BRANCH_PREFIX + tag_or_point


class Tut(object):

    def __init__(self, path):
        self.__path = path

    def _git_dir(self):
        """Return the actual location of the git dir for the repo.

        For submodules, this may be nested in a parent .git directory.

        """

        dotgit = os.path.join(self.__path, '.git')
        assert os.path.exists(dotgit)

        if os.path.isdir(dotgit):
            return dotgit

        # .git is a file, which means we're probably in a submodule.
        with file(dotgit, 'r') as gitfile:
            for line in gitfile:
                if line.startswith('gitdir: '):
                    return os.path.join(
                        self.__path,
                        line.strip().split('gitdir: ', 1)[1]
                    )

        raise Exception("Could not determine the location of the git repo.")

    def _repo_dirty(self):
        """Return True if the repository is dirty."""

        UNCHANGED_STATUSES = (' ', '?', '!')

        for status_line in git.status(porcelain=True):
            if not(status_line[0] in UNCHANGED_STATUSES and
                   status_line[1] in UNCHANGED_STATUSES):
                return True

        return False

    def _hooks_installed(self):
        """Return True if the tut hooks are installed in the Repo."""

        # right now just make sure some post-rewrite hook is installed
        return os.path.exists(
            os.path.join(self._git_dir(), 'hooks', 'post-rewrite')
        )

    def init(self):
        """Create a new repository with an initial commit."""

        cwd = os.getcwd()

        git.init(self.__path)

        os.chdir(self.__path)
        git.commit(
            m='Initializing empty Tut project.',
            allow_empty=True,
        )

        os.chdir(cwd)

    def install_hooks(self):
        """Install git hooks for tut."""

        # install the special post-rewrite hook
        hook_target = which('tut_remap')
        if not hook_target:
            # look for it alongside ourselves
            if os.path.exists(
                    os.path.join(
                        os.path.dirname(sys.argv[0]),
                        'tut_remap',
                    )
            ):
                hook_target = os.path.join(
                    os.path.dirname(sys.argv[0]),
                    'tut_remap',
                )

        if hook_target:
            os.symlink(
                os.path.abspath(hook_target),
                os.path.join(self._git_dir(), 'hooks', 'post-rewrite'),
            )

    def points(self):
        """Return a list of existing checkpoints (tags)."""

        tut_points = [
            tag.strip() for tag in git.tag(
                # '-n1',  # maybe n=1 would work, too
                _iter=True,
            )
        ]

        return tut_points

    def _branches(self):

        return [
            b.split()[-1].strip()
            for b in git.branch('-q')
        ]

    def _editting(self, name):
        """Return True if an edit is in progress for point_name."""

        return branch_name(name) in self._branches()

    def _commit_all_and_tag(self, message, tag_name, force=False):
        """Commit all changes in the working tree and tag with tag_name."""

        # commit all changes
        git.commit(
            all=True,
            m=message,
        )

        # tag the checkpoint
        git.tag(tag_name, force=force)

    def checkpoint(self, name, message=None):
        """Create a new checkpoint, or apply edits to an existing one."""

        if name in self.points():
            if self._editting(name):
                return self.finish_edit(name, message)
            else:
                raise Exception("Point already exists")

        if message is None:
            # generate a default message
            message = 'Tut Checkpoint: %s' % name

        self._commit_all_and_tag(message, name)

    def edit(self, name):
        """Start editing the checkpoint point_name."""

        if not self._hooks_installed():
            raise Exception(
                "Tut hook not installed; do you need to run tut init?"
            )

        # make sure this is a known checkpoint
        if name not in self.points():
            raise Exception("Unknown checkpoint.")

        # make sure the repo is clean
        if self._repo_dirty():
            raise Exception("Dirty tree.")

        # create a new branch to contain editing
        git.checkout(
            name,
            b=branch_name(name),
        )

    def finish_edit(self, name, message=None):
        """Complete an edit in progress and rebase any future points."""

        if message is None:
            # generate a default message
            message = 'Tut Checkpoint: %s' % name

        self._commit_all_and_tag(message, name, force=True)

        # rebase master onto our branch
        git.rebase(
            branch_name(name),
            'master',
        )

        # delete the editing branch
        git.branch('-d', branch_name(name))

    def move_checkpoints(self, old_sha, new_sha):
        """Move any checkpoints that point at old_sha to new_sha."""

        for tag_name in git.tag('--points-at=%s' % old_sha, _iter=True):
            tag_name = tag_name.strip()

            print git.tag(
                tag_name,
                new_sha,
                force=True,
            )
