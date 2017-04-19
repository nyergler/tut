from docutils.nodes import reference

from tut import version
from tut.sphinx.checkpoint import (
    TutDefaults,
    TutCheckpoint,
    initialize,
    cleanup,
)
from tut.sphinx.content import (
    TutContent,
    TutExec,
)
from tut.sphinx.code import (
    TutCodeDiff,
    TutLiteralInclude,
)


def setup(app):

    app.add_directive('tut', TutDefaults)
    app.add_directive('tut:exec', TutExec)
    app.add_directive('tut:content', TutContent)
    app.add_directive('checkpoint', TutCheckpoint)
    app.add_directive('tut:checkpoint', TutCheckpoint)
    app.add_directive('tut:literalinclude', TutLiteralInclude)
    app.add_directive('tut:diff', TutCodeDiff)

    app.connect('builder-inited', initialize)
    app.connect('build-finished', cleanup)

    return {
        'version': version(),
        'parallel_read_safe': False,
    }
