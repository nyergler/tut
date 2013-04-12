=====
 Tut
=====

**Tut** is a tool that helps you write tutorial style documentation
using Sphinx_.

Tutorial style documentation is documentation where sections build on
one another, and include code examples along the way. *Tut* helps you
manage the code in the tutorial as you write it, and include the
correct segments in your document.

Tut makes it easy to manage a git_ source repository for your
tutorial's code by using branches_ to record different steps. As you
write the code for your tutorial, Tut lets you include code from a
particular branch (or tag or commit) in your Sphinx document using the
built-in literalinclude_ directive.

Tut consists of two pieces: a program to manage branches, and a Sphinx
extension to switch branches during the Sphinx build.

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


Managing Branches
=================

In addition to making it easy to switch between branches or tags in
your source, **Tut** provides a tool for managing branches in the
repository. Tutorials usually have "steps" -- discreet units that
build upon previous ones -- and Tut models those as branches\ [1]_.
Each step's branch forks from the previous step's branch. Note that
use of the Tut command line tool is completely optional: Tut works
great with Sphinx and git on their own.

To start using Tut, run ``tut init <path>``::

  $ tut init ./demosrc

If the path (``./demosrc``) is not an existing git repository, Tut
will initialize one and add an initial commit.

When you want to start a new step (checkpoint) starting from the one
you're currently on, run ``tut start``::

  $ tut start step_one

After you've made checkpoints in your repository, you can run ``tut
points`` to list the checkpoints::

  $ tut points
  step_one
  step_two

If you realize you've made a mistake and want to change the code at an
earlier checkpoint, simply run ``tut edit``::

  $ tut edit step_one

Tut will check out the ``step_one`` branch, and you can make changes
and commit them. Once you're done editing, you'll want to roll those
changes forward, through the subsequent steps.

::

  $ tut next --merge

Running ``tut next`` will find the next step and check out that
branch. Adding ``--merge`` will also merge the previous step. If we're
done making changes to ``step_one``, running ``tut next --merge`` will
move us to ``step_two`` and merge ``step_one``.

.. [1] Tut 0.1 modeled these as tags, but after some experience with
   managing third party contributions, branches appear to be more
   flexible and useful.

.. _Sphinx: http://sphinx-doc.org/
.. _branches: http://git-scm.com/book/en/Git-Branching-Basic-Branching-and-Merging
.. _git: http://git-scm.org/
.. _literalinclude: http://sphinx-doc.org/markup/code.html#directive-literalinclude
