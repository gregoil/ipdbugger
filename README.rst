ipdbugger
---------
.. image:: https://travis-ci.org/gregoil/ipdbugger.svg?branch=master
    :target: https://travis-ci.org/gregoil/ipdbugger


``ipdbugger`` is a code debugging tool based on ``ipdb``.

Use the ``debug`` decorator on functions or classes to debug them.
What actually happens: it surrounds each statement of the functions with a
try-except, and starts an ipdb session in the exception handling section.

Installing
==========

.. code-block:: console

    $ pip install ipdbugger

Using
=====

.. code-block:: python

    from ipdbugger import debug

    @debug
    def f():
        foo = 1 + 1
        bar = 1 / 0
        baz = 2 + 2

Now when you run ``f()``, you'll get into an ipdb shell right after the
error (the division by zero):

.. code-block:: pycon

    >>> from ipdbugger import debug
    >>> @debug
        def f():
            foo = 1 + 1
            bar = 1 / 0
            baz = 2 + 2

    >>> f()
    Traceback (most recent call last):
       File "<ipython-input-2-5720bb02ab1d>", line 4, in f
        bar = 1 / 0
     ZeroDivisionError: integer division or modulo by zero
    > <ipython-input-2-5720bb02ab1d>(5)f()
          2 def f():
          3     foo = 1 + 1
          4     bar = 1 / 0
    ----> 5     baz = 2 + 2
          6

    ipdb> foo
    2
    ipdb>

From there, you have a couple of choices:

* ``retry`` the action
* ``continue`` with the rest of the flow (and ignore the error)
* ``raise`` the exception, as if you didn't catch it at all
* Use any other of the available ``ipdb`` commands, like ``jump``
