=====
 Tut
=====

**Tut** is a Sphinx_ extension that helps you write tutorial style
documentation. Tutorial style documentation is documentation where
sections build on one another, and include code examples along the
way. *Tut* helps you manage the code in the tutorial as you write it,
and include the correct segments in your document.

How does *Tut* help you? *Tut* provides the following features:

- Denote where each step begins, and helps you manage your git
  workflow by letting you start new steps and switch between steps.

  $ tut points
  $ tut checkpoint step_identifier
  $ tut steps
  - step_indentifier <1as85d>

- *Tut* works with git: when you create a new step, *Tut* records the
   current SHA as the starting point for that step. You can then work
   on the next step. If you want to make changes to a previous step,
   just switch back to it.

   $ tut switch step_one
   Switching to step_one... done.

- When you're done working on step_one, you can switch to another
  step, or jump to the end of the tutorial:

  $ tut switch end

- Note that if you're changing history, *Tut* will rebase_ your future
  steps onto the old step.


Within Sphinx you can denote where the steps begin::

  .. tut-step:: step_one
     :path: /path/to/code/repo

This means that any directives that refer to the filesystem after this
will be using the ``step_one`` state. So using ``literalinclude``, for
example, will include the source as it was in step one.



.. It'd be nice to figure out if there's going to be anything needed
.. to make the doctest builder work. Probably. Groups?


What I've semi-done:

* Checkpoint
* Edit checkpoints
* List checkpoints
* Maintain checkpoint tags after editing.
