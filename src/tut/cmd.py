"""Tut.

Usage:
  tut init [<path>]
  tut points
  tut checkpoint <name> [-m <message>]
  tut edit <name>

Options:
  -h --help     Show this screen.
  --version     Show version.

"""

from __future__ import absolute_import
import os
import sys

from docopt import docopt

import tut
from tut.model import Tut


def init(args):

    path = args.get('<path>')
    if path is None:
        path = os.getcwd()
    else:
        path = os.path.join(os.getcwd(), path)

    tut_repo = Tut(path)

    if not os.path.exists(os.path.join(path, '.git')):
        tut_repo.init()
    tut_repo.install_hooks()


def points(args):

    for point in Tut(os.getcwd()).points():
        print point


def checkpoint(args):

    point = Tut(os.getcwd()).checkpoint(
        args['<name>'],
        message=args.get('<message>'),
    )

    print "Recorded checkpoint: %s" % point


def edit(args):

    Tut(os.getcwd()).edit(
        args['<name>'],
    )


CMD_MAP = {
    'init': init,
    'points': points,
    'checkpoint': checkpoint,
    'edit': edit,
}


def main():
    arguments = docopt(__doc__, version='Tut %s' % tut.version())
    #print arguments

    for cmd in CMD_MAP:
        if arguments.get(cmd):
            CMD_MAP[cmd](arguments)
            break


def post_rewrite():

    tut = Tut(os.getcwd())

    for line in sys.stdin:
        rewrite = line.split()
        tut.move_checkpoints(rewrite[0].strip(), rewrite[1].strip())


if __name__ == '__main__':
    main()
