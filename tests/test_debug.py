"""Unit tests for the debug decorator in ipdbugger module."""
from __future__ import absolute_import

import pytest
from IPython.utils.capture import capture_output

from ipdbugger import debug

try:
    from unittest.mock import patch

except ImportError:
    from mock import patch


def test_debugging_raising_function():
    """Test debugging a raising function."""
    @debug
    def should_raise():
        raise Exception()

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        should_raise()
        assert set_trace.called


def test_debugging_raising_method():
    """Test debugging a raising bounded-method."""
    class A(object):
        def should_raise(self):
            raise Exception()

    a = A()
    a.should_raise = debug(a.should_raise)

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        a.should_raise()
        assert set_trace.called


def test_debugging_function_twice():
    """Test applying `debug` on a function more than once can be done."""
    @debug
    @debug
    def should_raise():
        raise Exception()

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        should_raise()
        assert set_trace.called_once


def test_debugging_non_raising_function():
    """Test debugging on a non-raising function."""
    @debug
    def non_raising_function():
        pass

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        non_raising_function()
        assert not set_trace.called


def test_debugging_class():
    """Test debugging a class with two methods."""
    @debug
    class DebuggedClass(object):
        def first_method(self):
            raise Exception()

        def second_method(self):
            raise Exception()

    debugged_object = DebuggedClass()

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        debugged_object.first_method()
        assert set_trace.called

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        debugged_object.second_method()
        assert set_trace.called


def test_debugging_non_compatible_type():
    """Test raising an indicative error when trying to debug a bad type."""
    with pytest.raises(TypeError,
                       match="Debugger can only wrap functions and classes. "
                             "Got object 1 of type int"):
        debug(1)


def test_debugging_when_source_code_is_missing():
    """Test debugging code that its source code is not available.

    Note:
        In this kind of code we cannot stop at an error, so we fall-back to
        simply running this code without interference.
    """
    exec("def function(): 1 / 0", locals(), globals())
    func = debug(globals()["function"])

    with pytest.raises(ArithmeticError):
        func()


def test_ignoring_exceptions():
    """Test ignoring specific exceptions that should be raised."""
    def func():
        raise ValueError()

    func = debug(func, ignore_exceptions=[ValueError])

    with pytest.raises(ValueError):
        func()


def test_targeting_specific_exception():
    """Test targeting specific exception that we should stop at it."""
    def func():
        assert False

    func = debug(func, catch_exception=AssertionError)

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        func()
        assert set_trace.called


def test_non_targeted_exceptions():
    """Test raising exceptions that don't match the targeted exception."""
    def func():
        raise ValueError()

    func = debug(func, catch_exception=AssertionError)

    with pytest.raises(ValueError):
        func()


def test_ignoring_excepted_exceptions():
    """Test ignoring exceptions that should be excepted."""
    @debug
    def func():
        try:
            raise ValueError()
        except ValueError:
            pass

    func()


def test_ignoring_excepted_exceptions_only_on_try_except_scope():
    """Test ignoring exceptions that should be only on try except scope."""
    def func():
        try:
            pass
        except ValueError:
            pass

        raise ValueError()

    func = debug(func)

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        func()
        assert set_trace.called


def test_wrapping_try_except_statement():
    """Test that try except statement also wrapped with ipdbugger."""
    @debug
    def func():
        try:
            raise ValueError()
        except ValueError:
            raise

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        func()
        assert set_trace.called_once


def test_wrapping_try_except_statement():
    """Test wrapping try except statement with no specific exception
        type excepted."""
    @debug
    def func():
        try:
            raise ValueError()
        except:
            pass

    func()
