from tut.sphinx.checkpoint import (
    TutDefaults,
    TutCheckpoint,
    initialize,
    cleanup,
)


def setup(app):

    app.add_directive('tut', TutDefaults)
    app.add_directive('checkpoint', TutCheckpoint)

    app.connect('builder-inited', initialize)
    app.connect('build-finished', cleanup)
