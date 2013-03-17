=====
 Tut
=====

**Tut** is a tool that helps you write tutorial style documentation
using Sphinx_.

Tutorial style documentation is documentation where sections build on
one another, and include code examples along the way. *Tut* helps you
manage the code in the tutorial as you write it, and include the
correct segments in your document.

Tut makes it easy to manage tags_ in a git_ source repository, and
include code from a specific tag (or branch or commit) in your Sphinx
document using the built-in literalinclude_ directive. Tut consists of
two pieces: a program to manage tags, and a Sphinx extension to switch
tags during the Sphinx build.

Including Code in Sphinx
========================

Sphinx provides the literalinclude_ directive, which allows you to
include source files, or parts of files, in your documentation. Tut
allows you to switch to a specific git tag, branch, or commit before
processing the inclusion.

To enable Tut, add ``tut.sphinx`` to the list of enabled extensions in
your Sphinx project's ``conf.py`` file::

  extensions = [
      # ...
      'tut.sphinx',
  ]

The ``checkpoint`` directive takes a single argument, which is the git
reference to switch to. For example, the following directive will
checkout ``step_one`` (either a branch or tag) in the git repository
in ``/src``::

  .. checkpoint:: step_one
     :path: /src

The directive doesn't result in any output, but ``literalinclude`` (or
other file-system inclusion directives) that come after the
``checkpoint`` will use the newly checked-out version.

If your document contains multiple checkpoints, you can specify the
path once using the ``tut`` directive::

  .. tut::
     :path: /src

Note that ``/src`` is evaluated using the same rules as govern
literalinclude_. That is, the file name is usually relative to the
current file’s path. However, if it is absolute (starting with /), it
is relative to the top source directory.

**Tut** records the starting state of repositories the first time it
does a checkout, and restores the initial state after the build completes.


Restrictions
------------

When Sphinx encounters a ``checkpoint`` directive, it performs a ``git
checkout`` in target repository. This means that the repository should
not contain uncommitted changes, to avoid errors on checkout.


Managing Tags
=============

In addition to making it easy to switch between tags in your source
repository, **Tut** provides a tool for managing those tags. The
primary advantage of using Tut to manage your tags is that it provides
support for rolling back history to make changes, and keeping
subsequent tags intact.

To start using Tut, run ``tut init <path>``::

  $ tut init ./demosrc

If the path (``./demosrc``) is an existing git repository, Tut will
install its `post-rewrite`_ hook. If it is not an existing repository,
Tut will create the repository, install the hook, and add a first
commit.

When you've made some changes and want to create a checkpoint, simple
run ``tut checkpoint``::

  $ tut checkpoint step_one

You can optionally specify a commit message::

  $ tut checkpoint step_one -m "The first checkpoint."

Under the hood, Tut is executing something like ``git commit -a``.

After you've made checkpoints in your repository, you can run ``tut
points`` to list the checkpoints::

  $ tut points
  step_one
  step_two

If you realize you've made a mistake and want to change the code at an
earlier checkpoint, simply run ``tut edit``::

  $ tut edit step_one

Tut will roll back your repository to the ``step_one`` tag, and put
you on a branch for editing. Once you've finished editing, commit the
changes using ``tut checkpoint`` again::

  $ tut checkpoint step_one -m "Edited Step One."

Tut will commit your changes, and then apply the future changes on top
of them. The Tut post-rewrite hook will ensure that the tags
(checkpoints) that come after ``step_one`` are updated to reflect
their new SHAs.

.. _Sphinx: http://sphinx-doc.org/
.. _tags: http://git-scm.com/book/en/Git-Basics-Tagging
.. _git: http://git-scm.org/
.. _`post-rewrite`: https://www.kernel.org/pub/software/scm/git/docs/githooks.html
.. _literalinclude: http://sphinx-doc.org/markup/code.html#directive-literalinclude
