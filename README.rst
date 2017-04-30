=====
 Tut
=====

.. image:: https://travis-ci.org/nyergler/tut.svg?branch=master
  :target: https://travis-ci.org/nyergler/tut

.. image:: https://coveralls.io/repos/github/nyergler/tut/badge.svg?branch=master
  :target: https://coveralls.io/github/nyergler/tut?branch=master


**Tut** is a tool that helps you write technical documentation using Sphinx_ 1.6 and later.

**Tut** provides a workflow that supports tutorial-style documents particularly well. If your writing includes code samples that build on one another, Tut is for you. **Tut** helps you manage the code in the tutorial as you write it, and include the correct segments in your document.

**Tut** makes it easy to manage a git_ source repository for your tutorial's code by using branches_ to record different steps. As you write the code for your tutorial, **Tut** allows you to include code from a particular step in your Sphinx document. **Tut** also has basic support for showing the difference between two branches, allowing you to effectively show what's changed in a way that's readable for humans.

**Tut** consists of two pieces: a program to manage branches, and a Sphinx
extension to switch branches during the Sphinx build.


Using Tut
=========

I wrote **Tut** because I wanted an easier way to manage the sample code I was writing for `Effective Django`_. I was using ``git`` to track my changes to the text, but those changes weren't the ones I was reflecting in the code: I could use git to tell me what changed in the text between two points in time, but I couldn't easily tell what changed between chapters. The code, in effect, was a parallel set of changes, and I was interested in understanding them over the course of the text, not (necessarily) over the course of my writing timeline.

**Tut** is a command-line tool that makes managing the code changes independently of the text changes more straight-forward. It allows you to define a set of "points" in the development of your source and switch back and forth between them. If you make a change to an early point in your code, you can roll that change forward so your future code is consistent. Under the hood **Tut** uses ``git``, so you can include your code as a sub-module and use the other git tools you've come to appreciate.

To start using **Tut**, run ``tut init <path>``::

  $ tut init ./demosrc

If the path (``./demosrc``) is not an existing git repository, **Tut**
will initialize one and add an initial commit.

Subsequent **Tut** commands should be run from within the **Tut**-managed
repository.

::

  $ cd demosrc

To start a point from your current position, run ``tut start``::

  $ tut start step_one

After you've created different points in your repository, you can run ``tut points`` to list them::

  $ tut points
  step_one
  step_two

If you realize you've made a mistake and want to change the code at an
earlier checkpoint, simply run ``tut edit``::

  $ tut edit step_one

**Tut** will check out the ``step_one`` branch, and you can make changes and commit them. Once you're done editing, commit your changes using ``git``. You'll also want to roll those changes forward, through the subsequent steps.

::

  $ tut next --merge

Running ``tut next`` will find the next step and check out that
branch. Adding ``--merge`` will also merge the previous step. If we're
done making changes to ``step_one``, running ``tut next --merge`` will
move us to ``step_two`` and merge ``step_one``.

Including Code in Sphinx
========================

Sphinx provides the literalinclude_ directive, which allows you to
include source files, or parts of files, in your documentation. **Tut**
allows you to switch to a specific git tag, branch, or commit before
processing the inclusion.

To enable **Tut**, add ``tut.sphinx`` to the list of enabled extensions in
your Sphinx project's ``conf.py`` file::

  extensions = [
      # ...
      'tut.sphinx',
  ]

The ``checkpoint`` directive takes a single argument, which is the git
reference to switch to. For example, the following directive will
checkout ``step_one`` (either a branch or tag) in the git repository
in ``/src``::

  .. tut:checkpoint:: step_one
     :path: /src

The directive doesn't result in any output, but ``literalinclude`` (or
other file-system inclusion directives) that come after the
``checkpoint`` will use the newly checked-out version.

**Tut** records the starting state of repositories the first time it
does a checkout, and restores the initial state after the build completes.

If your document contains multiple checkpoints, you can specify the
path once using the ``tut`` directive::

  .. tut::
     :path: /src

Note that ``/src`` is evaluated using the same rules as govern
literalinclude_. That is, the file name is usually relative to the
current file’s path. However, if it is absolute (starting with /), it
is relative to the top source directory.

Within a checkpoint **Tut** provides two new directives for fetching content: ``tut:literalinclude`` and ``tut:diff``.

``tut:literalinclude`` works a lot like Sphinx's built-in literalinclude_ directive. However, instead of loading the file from the filesystem directly, ``tut:literalinclude`` retrieves it from the git repository.

For example::

  .. tut:checkpoint:: step_two
     :path: /src

     ...

  .. tut:literalinclude:: setup.py

Will fetch ``setup.py`` from the ``step_two`` branch in the git repository located at ``/src``.

**Tut** can also show the changes between two checkpoints (branches) using the ``tut:diff`` directive. Like ``tut:literalinclude`` it uses the git repository referenced in the last checkpoint by default. You can specify the ``ref`` and ``prev_ref`` to compare; if omitted, ``ref`` defaults to the current checkpoint and ``prev_ref`` defaults to the previous point, as listed in the output of ``tut points``.

::

  .. tut:diff:: setup.py
    :ref: step_two
    :prev_ref: step_one
    :path: /src/demosrc


N.B.
====

When Sphinx encounters a ``checkpoint`` directive, it performs a ``git
checkout`` in target repository. This means that the repository should
not contain uncommitted changes, to avoid errors on checkout.

Note that this will probably change soon, to allow for more flexible use of content from the git repository.


.. _`Effective Django`: http://www.effectivedjango.com/
.. _Sphinx: http://sphinx-doc.org/
.. _branches: http://git-scm.com/book/en/Git-Branching-Basic-Branching-and-Merging
.. _git: http://git-scm.org/
.. _literalinclude: http://sphinx-doc.org/markup/code.html#directive-literalinclude
