"""Unit tests for the debug decorator in ipdbugger module."""
from __future__ import absolute_import

from IPython.utils.capture import capture_output
import pytest

from ipdbugger import debug, IPDBugger

try:
    from unittest.mock import patch

except ImportError:
    from mock import patch


def test_debugging_raising_function():
    @debug
    def should_raise():
        raise Exception()

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        should_raise()
        assert set_trace.called


def test_debugging_raising_method():
    class A(object):
        def should_raise(self):
            raise Exception()

    a = A()
    a.should_raise = debug(a.should_raise)

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        a.should_raise()
        assert set_trace.called


def test_debugging_function_twice():
    @debug
    @debug
    def should_raise():
        raise Exception()

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        should_raise()
        assert set_trace.called_once


def test_debugging_non_raising_function():
    @debug
    def non_raising_function():
        pass

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        non_raising_function()
        assert not set_trace.called


def test_debugging_class():
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
    with pytest.raises(TypeError,
                       match="Debugger can only wrap functions and classes. "
                             "Got object 1 of type int"):
        debug(1)


def test_debugging_when_source_code_is_missing():
    exec("def function(): 1 / 0", locals(), globals())
    func = debug(globals()["function"])

    with pytest.raises(ArithmeticError):
        func()


def test_ignoring_exceptions():
    def func():
        raise ValueError()

    func = debug(func, ignore_exceptions=[ValueError])

    with pytest.raises(ValueError):
        func()


def test_targeting_specific_exception():
    def func():
        assert False

    func = debug(func, catch_exception=AssertionError)

    with capture_output(), patch('bdb.Bdb.set_trace') as set_trace:
        func()
        assert set_trace.called


def test_non_targeted_exceptions():
    def func():
        raise ValueError()

    func = debug(func, catch_exception=AssertionError)

    with pytest.raises(ValueError):
        func()
