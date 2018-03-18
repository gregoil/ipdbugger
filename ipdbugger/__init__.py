"""This module contains code debugging tools, inspired by the 'fuckit' package.

Use the `debug` decorator on functions or classes to debug them.
What actually happens: it surrounds each statement of the functions with a
try-except, and starts an ipdb session in the exception handling section.

Usage notes (while in ipdb):
* Looking at variables:
    Use 'up' and 'down' to move in the traceback frames.
* Code debugging / running:
    You can use 'jump' to move inside the frame, and use 'next' or 'continue'
    to continue running.
* Continue the run to dismiss the exception.
* Call 'raise' to let the exception raise.
* Call 'retry' to redo the previous line.
"""
# pylint: disable=misplaced-bare-raise,protected-access,bare-except
# pylint: disable=missing-docstring,too-many-locals,too-many-branches
import re
import ast
import sys
import types
import inspect
import functools
import traceback

import colorama
from termcolor import colored
from IPython.core.debugger import Pdb

# Enable color printing on screen.
colorama.init()


class IPDBugger(Pdb):
    """Deubbger class, adds functionality to the normal pdb."""
    def do_raise(self, arg):
        """Raise the last exception caught."""
        self.do_continue(arg)
        _, exc_value, _ = sys.exc_info()
        exc_value._ipdbugger_let_raise = True
        raise

    def do_retry(self, arg):
        """Rerun the previous command."""
        prev_line = self.curframe.f_lineno - 1
        # Make sure not to jump to the middle of the previous statement
        while True:
            try:
                self.curframe.f_lineno = prev_line
                break

            except:
                prev_line -= 1

        self.do_jump(prev_line)
        self.do_continue(arg)
        return 1

    def dispatch_line(self, frame):
        """Handle line action and return the next line callback."""
        callback = Pdb.dispatch_line(self, frame)

        # If the ipdb session ended, don't return a callback for the next line
        if self.stoplineno == -1:
            return None

        return callback


def start_debugging():
    """Start a debugging session after catching an exception.

    This prints the traceback and start ipdb session in the frame of the error.
    """
    exc_type, exc_value, exc_tb = sys.exc_info()

    if hasattr(exc_value, '_ipdbugger_let_raise'):
        raise

    print
    for line in traceback.format_exception(exc_type, exc_value, exc_tb):
        print colored(line, 'red'),

    # Get the frame with the error.
    test_frame = sys._getframe(-1).f_back

    from ipdb.__main__ import wrap_sys_excepthook, def_colors
    wrap_sys_excepthook()
    IPDBugger(def_colors).set_trace(test_frame)


class ErrorsCatchTransformer(ast.NodeTransformer):
    """Surround each statement with a try/except block to catch errors.

    Attributes:
        IGNORED_EXCEPTION (str): name of the base class of the exceptions
             to catch, or None to catch all.
    """
    def __init__(self, ignore_exceptions=(), catch_exception=None):
        raise_cmd = ast.Raise()
        start_debug_cmd = ast.Expr(
            value=ast.Call(ast.Name("start_debugging", ast.Load()), [], [],
                           None, None))

        catch_exception_node = None
        if catch_exception is not None:
            catch_exception_node = ast.Name(catch_exception.__name__,
                                            ast.Load())

        self.exception_handlers = [ast.ExceptHandler(type=catch_exception_node,
                                                     name=None,
                                                     body=[start_debug_cmd])]

        for exception_class in ignore_exceptions:
            ignore_exception_node = ast.Name(exception_class.__name__,
                                             ast.Load())

            self.exception_handlers.insert(
                0,
                ast.ExceptHandler(type=ignore_exception_node,
                                  name=None,
                                  body=[raise_cmd]))

    def generic_visit(self, node):
        """Surround node statement with a try/except block to catch errors.

        This method is called for every node of the parsed code, and only
        changes statement lines.

        Args:
            node (ast.AST): node statement to surround.
        """
        super(ErrorsCatchTransformer, self).generic_visit(node)

        if (isinstance(node, ast.stmt) and
                not isinstance(node, ast.FunctionDef)):
            new_node = ast.TryExcept(
                orelse=[],
                body=[node],
                handlers=self.exception_handlers)

            return ast.copy_location(new_node, node)

        return node


def debug(victim, ignore_exceptions=(), catch_exception=None):
    """A decorator function to catch exceptions and enter debug mode.

    Args:
        victim (object): either a class or function to wrap and debug.
        ignore_exceptions (list): list of classes of exceptions not to catch.
        catch_exception (type): class of exception to catch and debug.
            default is None, meaning catch all exceptions.

    Returns:
        object. wrapped class or function.

    Note:
        This wrapper avoids recursion by setting a flag to each wrapped item.
    """
    if inspect.isfunction(victim):
        if hasattr(victim, '_ipdebug_wrapped'):
            # Don't wrap the function more than once
            return victim

        _transformer = ErrorsCatchTransformer(
            ignore_exceptions=ignore_exceptions,
            catch_exception=catch_exception)

        try:
            # Try to get the source code of the wrapped object.
            sourcelines, start_num = inspect.getsourcelines(victim.func_code)
            indent = re.match(r'\s*', sourcelines[0]).group()
            source = ''.join(l.replace(indent, '', 1) for l in sourcelines)

        except IOError:
            # Worst-case scenario we can only catch errors at a granularity
            # of the whole function
            @functools.wraps(victim)
            def wrapper(*args, **kw):
                victim(*args, **kw)

            return wrapper

        else:
            # If we have access to the source, we can silence errors on a
            # per-expression basis, which is "better"

            old_code_tree = ast.parse(source)
            # Reposition the line numbers to their original value
            ast.increment_lineno(old_code_tree, start_num - 1)
            tree = _transformer.visit(old_code_tree)

            import_debug_cmd = ast.ImportFrom(
                __name__, [ast.alias("start_debugging", None)], 0)

            # Add import to the debugger as first command
            tree.body[0].body.insert(0, import_debug_cmd)

            # Add import to the exception classes
            if catch_exception is not None:
                import_exception_cmd = ast.ImportFrom(
                    catch_exception.__module__,
                    [ast.alias(catch_exception.__name__, None)], 0)

                tree.body[0].body.insert(1, import_exception_cmd)

            for exception_class in ignore_exceptions:
                import_exception_cmd = ast.ImportFrom(
                    exception_class.__module__,
                    [ast.alias(exception_class.__name__, None)], 0)

                tree.body[0].body.insert(1, import_exception_cmd)

            # Delete the debugger decorator of the function
            del tree.body[0].decorator_list[:]

            # Index of the function (first original command in it)
            first_command_index = 1 + len(ignore_exceptions)
            if catch_exception is not None:
                first_command_index += 1

            # Add pass at the end (to enable debugging the last command)
            pass_cmd = ast.Pass()
            func_body = tree.body[0].body
            pass_cmd.lineno = func_body[-1].lineno + 1  # Next of the last line
            pass_cmd.col_offset = func_body[first_command_index].col_offset
            func_body.insert(len(func_body), pass_cmd)

            # Fix missing line numbers and column offsets before compiling
            for node in ast.walk(tree):
                if not hasattr(node, 'lineno'):
                    node.lineno = 0

            ast.fix_missing_locations(tree)

            # Create a new runnable code object to replace the original code
            code = compile(tree, victim.func_code.co_filename, 'exec')
            victim.func_code = code.co_consts[0]

            # Set a flag to indicate that the method was wrapped
            victim._ipdebug_wrapped = True

            return victim

    elif inspect.ismethod(victim):
        debug(victim.im_func, ignore_exceptions, catch_exception)
        return victim

    elif isinstance(victim, (types.ClassType, type)):
        # Wrap each method of the class with the debugger
        for name, member in victim.__dict__.items():
            if isinstance(member, (types.ClassType, types.FunctionType,
                                   types.LambdaType, types.MethodType)):

                setattr(victim, name,
                        debug(member, ignore_exceptions, catch_exception))

        return victim

    else:
        raise RuntimeError("Debugger can only wrap functions and classes")

    return victim
