"""Unit tests for the debug decorator in ipdbugger module."""
from __future__ import absolute_import

import sys

import pytest

from ipdbugger import debug

try:
    from unittest.mock import patch, MagicMock

except ImportError:
    from mock import patch, MagicMock


def test_debugging_raising_function():
    """Test debugging a raising function."""
    @debug
    def should_raise():
        raise Exception()

    with patch('ipdbugger.start_debugging') as set_trace:
        should_raise()
        assert set_trace.called


def test_debugging_raising_method():
    """Test debugging a raising bounded-method."""
    class A(object):
        def should_raise(self):
            raise Exception()

    a = A()
    a.should_raise = debug(a.should_raise)

    with patch('ipdbugger.start_debugging') as set_trace:
        a.should_raise()
        assert set_trace.called


def test_debugging_function_twice():
    """Test applying `debug` on a function more than once can be done."""
    @debug
    @debug
    def should_raise():
        raise Exception()

    with patch('ipdbugger.start_debugging') as set_trace:
        should_raise()
        assert set_trace.called_once


def test_debugging_non_raising_function():
    """Test debugging on a non-raising function."""
    @debug
    def non_raising_function():
        pass

    with patch('ipdbugger.start_debugging') as set_trace:
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

    with patch('ipdbugger.start_debugging') as set_trace:
        debugged_object.first_method()
        assert set_trace.called

    with patch('ipdbugger.start_debugging') as set_trace:
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

    with patch('ipdbugger.start_debugging') as set_trace:
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

    with patch('ipdbugger.start_debugging') as set_trace:
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

    with patch('ipdbugger.start_debugging') as set_trace:
        func()
        assert set_trace.called_once


def test_wrapping_unbound_catch():
    """Test wrapping try except statement with no specific exception
        type excepted."""
    @debug
    def func():
        try:
            raise ValueError()
        except:
            pass

    func()


def test_wrapping_twice_with_try_except_statement():
    """Test wrapping try except within try except statement."""
    @debug
    def func():
        try:
            try:
                raise ValueError()
            except ValueError:
                pass

            raise KeyError()

        except KeyError:
            pass

    with patch('ipdbugger.start_debugging') as set_trace:
        func()
        assert set_trace.call_count == 0


def test_wrapping_function_with_closure():
    """Test wrapping a function with closure."""
    raise_exc = True

    @debug
    def func():
        if raise_exc:
            raise ValueError()

    with patch('ipdbugger.start_debugging') as set_trace:
        func()
        assert set_trace.called_once


class SaveFuncName(object):
    """Auxiliary class that saves the context's function name."""
    def __init__(self):
        self.func_name = None

    def __call__(self):
        self.func_name = sys._getframe(-1).f_back.f_code.co_name


def test_no_depth():
    """Test wrapping a function without propagating to lower calls."""
    def func_lowest():
        raise ValueError()
        pass

    def func_middle():
        func_lowest()
        pass

    def func_upper():
        func_middle()
        pass

    func_upper = debug(func_upper, depth=0)

    with patch('ipdbugger.start_debugging', SaveFuncName()) as name_saver:
        func_upper()
        assert name_saver.func_name == "func_upper"


def test_depth_one():
    """Test wrapping a function one more call level."""
    def func_lowest():
        raise ValueError()
        pass

    def func_middle():
        func_lowest()
        pass

    def func_upper():
        func_middle()
        pass

    func_upper = debug(func_upper, depth=1)

    with patch('ipdbugger.start_debugging', SaveFuncName()) as name_saver:
        func_upper()
        assert name_saver.func_name == "func_middle"


def test_depth_infinite():
    """Test wrapping a function infinite call levels."""
    def func_lowest():
        raise ValueError()
        pass

    def func_middle():
        func_lowest()
        pass

    def func_upper():
        func_middle()
        pass

    func_upper = debug(func_upper, depth=-1)

    with patch('ipdbugger.start_debugging', SaveFuncName()) as name_saver:
        func_upper()
        assert name_saver.func_name == "func_lowest"


def test_ignore_all_exceptions():
    """Test ignoring all exceptions."""
    def func():
        raise Exception()

    func = debug(func, ignore_exceptions=None)

    with pytest.raises(Exception):
        func()


def test_using_debug_as_decorator_with_kwargs():
    """Test using debug function as decorator with kwargs."""

    @debug(catch_exception=ValueError)
    def func():
        raise ValueError()

    with patch('ipdbugger.start_debugging') as set_trace:
        func()
        assert set_trace.called
