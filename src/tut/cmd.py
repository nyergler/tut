"""Tut.

Usage:
  tut init [<path>]
  tut start <name>
  tut points
  tut edit <name>
  tut next [--merge]

Options:
  -h --help     Show this screen.
  --version     Show version.

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


def init(args):

    path = args.get('<path>')
    if path is None:
        path = os.getcwd()
    else:
        path = os.path.join(os.getcwd(), path)

    tut_repo = Tut(path)

    if not os.path.exists(os.path.join(path, '.git')):
        tut_repo.init()


def start(args):

    Tut(os.getcwd()).start(args['<name>'])


def points(args):

    for point in Tut(os.getcwd()).points():
        print point


def edit(args):

    Tut(os.getcwd()).edit(
        args['<name>'],
    )


def next_step(args):

    Tut(os.getcwd()).next(merge=args.get('--merge'))


CMD_MAP = {
    'start': start,
    'init': init,
    'points': points,
    'edit': edit,
    'next': next_step,
}


def main():
    arguments = docopt(__doc__, version='Tut %s' % tut.version())

    for cmd in CMD_MAP:
        if arguments.get(cmd):
            try:
                CMD_MAP[cmd](arguments)
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
