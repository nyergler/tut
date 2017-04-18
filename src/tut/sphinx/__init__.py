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


def order_docs(app, env, docnames):
    """Force Sphinx to process documents in TOC order."""

    # TK: To get the complete ordering this will need to descend into the
    # referenced documents and inspect their toctrees

    try:
        toc = env.get_toctree_for(app.config.master_doc, app.builder, False)
    except FileNotFoundError:
        app.warn('No toctree available; consider re-building')
        toc = None

    if toc is None:
        return

    entries = toc.traverse(descend=True, condition=reference)

    remaining_docnames = env.found_docs.copy() - {app.config.master_doc}
    docnames.clear()
    docnames.append(app.config.master_doc)

    for entry in entries:
        if not entry.attributes.get('internal'):
            # not an internal reference
            continue

        docname = entry.attributes['refuri'].rsplit('#', 1)[0].rsplit('.', 1)[0]
        if docname in remaining_docnames:
            docnames.append(docname)
            remaining_docnames.remove(docname)

    if remaining_docnames:
        # there are documents not in the tree, emit a warning
        app.warn(
            'Some documents are not able to be explicitly ordered; consider re-building.',
            remaining_docnames,
        )

        docnames.extend(list(remaining_docnames))


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
    app.connect('env-before-read-docs', order_docs)

    return {
        'version': version(),
        'parallel_read_safe': False,
    }
