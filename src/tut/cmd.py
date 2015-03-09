"""Tut.

Usage:
  tut init [<path>]     Initialize <path> as a Tut project.
  tut fetch <remote>
  tut start <name>      Start a new step, <name>, based on the current one.
  tut points            List the steps, in order.
  tut edit <name>       Begin editing the files for step <name>.
  tut next [--merge]    Move to the next step, option merging.

Options:
  -h --help             Show this screen.
  --version             Show version.

"""

from __future__ import absolute_import
import os
import sys

from docopt import docopt

import tut
from tut.model import (
    Tut,
    TutException,
)


def init(tut, args):

    path = args.get('<path>')
    if path is None:
        path = os.getcwd()
    else:
        path = os.path.join(os.getcwd(), path)

    tut_repo = Tut(path)

    if not os.path.exists(os.path.join(path, '.git')):
        tut_repo.init()


def fetch(tut, args):

    remote = args.get('<remote>')

    for point in tut.points(remote):
        tut.start(
            point.split('/')[-1],
            starting_point=point,
        )

def start(tut, args):

    tut.start(args['<name>'])


def points(tut, args):

    for point in tut.points():
        print point


def edit(tut, args):

    tut.edit(
        args['<name>'],
    )


def next_step(tut, args):

    tut.next(merge=args.get('--merge'))


CMD_MAP = {
    'start': start,
    'init': init,
    'points': points,
    'edit': edit,
    'next': next_step,
    'fetch': fetch,
}


def main():
    arguments = docopt(__doc__, version='Tut %s' % tut.version())

    for cmd in CMD_MAP:
        if arguments.get(cmd):
            try:
                CMD_MAP[cmd](
                    Tut(os.getcwd()),
                    arguments,
                )
            except TutException, e:
                print "Error: %s" % e
                sys.exit(1)

            break


def post_rewrite():

    tut = Tut(os.getcwd())

    for line in sys.stdin:
        rewrite = line.split()
        tut.move_checkpoints(rewrite[0].strip(), rewrite[1].strip())


if __name__ == '__main__':
    main()
