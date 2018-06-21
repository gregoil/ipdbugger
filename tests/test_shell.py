from __future__ import print_function

import bdb
import pytest
from IPython.utils.capture import capture_output

from ipdbugger import debug

try:
    from unittest import mock
except ImportError:
    import mock


@mock.patch("sys.stdin")
def test_help(stdin):
    """Test that both raise and retry actions are mentioned on help message."""
    @debug
    def some_func():
        raise ValueError("some error")

    stdin.readline.side_effect = ["help", "exit"]
    with capture_output() as out, pytest.raises(bdb.BdbQuit):
        some_func()

    assert "raise" in out.stdout
    assert "retry" in out.stdout


@mock.patch("sys.stdin")
def test_raise(stdin):
    """Test that exceptions can be raised back to the main program."""
    @debug
    def some_func():
        raise ValueError("some error")

    with pytest.raises(ValueError,
                       match="some error"):
        stdin.readline.return_value = "raise"
        some_func()


@mock.patch("sys.stdin")
def test_continue(stdin):
    """Test that program execution can continue after an error occurred."""
    @debug
    def some_func():
        raise ValueError("some error")

    stdin.readline.return_value = "continue"
    some_func()


@mock.patch("sys.stdin")
def test_retry(stdin):
    """Test retrying buggy actions."""
    class A:
        def __init__(self):
            self.count = 0

        @debug
        def func(self):
            self.sometimes_buggy()

        def sometimes_buggy(self):
            if self.count <= 1:
                self.count += 1
                raise ValueError("some error")

    stdin.readline.side_effect = ["retry", "continue"]
    a = A()
    a.func()

    assert a.count == 2
