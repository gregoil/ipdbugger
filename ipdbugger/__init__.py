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
from __future__ import print_function
from __future__ import absolute_import
# pylint: disable=no-member,not-callable
# pylint: disable=protected-access,bare-except
# pylint: disable=missing-docstring,too-many-locals,too-many-branches
import re
import ast
import sys
import types
import inspect
import traceback

import colorama
from termcolor import colored
from future.utils import raise_
from IPython.terminal.debugger import TerminalPdb

# Enable color printing on screen.
colorama.init()


IS_PYTHON_3 = sys.version_info > (3, 0)


class IPDBugger(TerminalPdb):
    """Debugger class, adds functionality to the normal pdb."""

    def __init__(self, exc_info, *args, **kwargs):
        TerminalPdb.__init__(self, *args, **kwargs)
        self.exc_info = exc_info

    def do_raise(self, arg):
        """Raise the last exception caught."""
        self.do_continue(arg)

        # Annotating the exception for a continual re-raise
        _, exc_value, _ = self.exc_info
        exc_value._ipdbugger_let_raise = True

        raise_(*self.exc_info)

    def do_retry(self, arg):
        """Rerun the previous command."""
        prev_line = self.curframe.f_lineno - 1
        # Make sure not to jump to the middle of the previous statement
        while True:
            try:
                self.curframe.f_lineno = prev_line
                break

            except ValueError:
                prev_line -= 1

        self.do_jump(prev_line)
        self.do_continue(arg)
        return 1

    def dispatch_line(self, frame):
        """Handle line action and return the next line callback."""
        callback = TerminalPdb.dispatch_line(self, frame)

        # If the ipdb session ended, don't return a callback for the next line
        if self.stoplineno == -1:
            return None

        return callback


def start_debugging():
    """Start a debugging session after catching an exception.

    This prints the traceback and start ipdb session in the frame of the error.
    """
    exc_type, exc_value, exc_tb = sys.exc_info()

    # If the exception has been annotated to be re-raised, raise the exception
    if hasattr(exc_value, '_ipdbugger_let_raise'):
        raise_(*sys.exc_info())

    print()
    for line in traceback.format_exception(exc_type, exc_value, exc_tb):
        print(colored(line, 'red'), end=' ')

    # Get the frame with the error.
    test_frame = sys._getframe(-1).f_back

    from ipdb.__main__ import wrap_sys_excepthook
    wrap_sys_excepthook()
    IPDBugger(exc_info=sys.exc_info()).set_trace(test_frame)


class ErrorsCatchTransformer(ast.NodeTransformer):
    """Surround each statement with a try/except block to catch errors."""

    def __init__(self, ignore_exceptions=(), catch_exception=None, depth=0):
        self.depth = depth
        self.catch_exception = None
        self.ignore_exceptions = None

        if ignore_exceptions is not None:
            self.ignore_exceptions = [exception_class.__name__
                                      for exception_class in ignore_exceptions]

        if catch_exception is not None:
            self.catch_exception = catch_exception.__name__

    @property
    def ast_try_except(self):
        return ast.Try if IS_PYTHON_3 else ast.TryExcept

    def wrap_with_try(self, node):
        """Wrap an ast node in a 'try' node to enter debug on exception."""
        handlers = []

        if self.ignore_exceptions is None:
            handlers.append(ast.ExceptHandler(type=None,
                                              name=None,
                                              body=[ast.Raise()]))

        else:
            ignores_nodes = [ast.Name(exception_class, ast.Load())
                             for exception_class in self.ignore_exceptions]

            handlers.append(ast.ExceptHandler(type=ast.Tuple(ignores_nodes,
                                                             ast.Load()),
                                              name=None,
                                              body=[ast.Raise()]))

            if self.catch_exception not in self.ignore_exceptions:
                call_extra_parameters = [] if IS_PYTHON_3 else [None, None]
                start_debug_cmd = ast.Expr(
                    value=ast.Call(ast.Name("start_debugging", ast.Load()),
                                   [], [], *call_extra_parameters))

                catch_exception_type = None
                if self.catch_exception is not None:
                    catch_exception_type = ast.Name(self.catch_exception,
                                                    ast.Load())

                handlers.append(ast.ExceptHandler(type=catch_exception_type,
                                                  name=None,
                                                  body=[start_debug_cmd]))

        try_except_extra_params = {"finalbody": []} if IS_PYTHON_3 else {}

        new_node = self.ast_try_except(orelse=[], body=[node],
                                       handlers=handlers,
                                       **try_except_extra_params)

        return ast.copy_location(new_node, node)

    def try_except_handler(self, node):
        """Handler for try except statement to ignore excepted exceptions."""
        # List all excepted exception's names
        excepted_types = []
        for handler in node.handlers:
            if handler.type is None:
                excepted_types = None
                break

            if isinstance(handler.type, ast.Tuple):
                excepted_types.extends([exception_type.id for exception_type
                                        in handler.type.elts])

            else:
                excepted_types.append(handler.type.id)

        new_exception_list = self.ignore_exceptions

        if self.ignore_exceptions is not None:
            if excepted_types is None:
                new_exception_list = None
            else:
                new_exception_list = list(set(excepted_types +
                                              self.ignore_exceptions))

        # Set the new ignore list, and save the old one
        old_exception_handlers, self.ignore_exceptions = \
            self.ignore_exceptions, new_exception_list

        # Run recursively on all sub nodes with the new ignore list
        node.body = [self.visit(node_item) for node_item in node.body]

        # Revert changes from ignore list
        self.ignore_exceptions = old_exception_handlers

    # pylint: disable=invalid-name
    def visit_Call(self, node):
        """Propagate 'debug' wrapper into inner function calls if needed.

        Args:
            node (ast.AST): node statement to surround.
        """
        if self.depth == 0:
            return node

        if self.ignore_exceptions is None:
            ignore_exceptions = ast.Name("None", ast.Load())

        else:
            exception_names = [ast.Name(exception, ast.Load())
                               for exception in self.ignore_exceptions]
            ignore_exceptions = ast.List(exception_names, ast.Load())

        catch_exception_type = self.catch_exception if self.catch_exception \
            else "None"

        catch_exception = ast.Name(catch_exception_type, ast.Load())
        depth = ast.Num(self.depth - 1 if self.depth > 0 else -1)

        debug_node_name = ast.Name("debug", ast.Load())
        call_extra_parameters = [] if IS_PYTHON_3 else [None, None]
        node.func = ast.Call(debug_node_name,
                             [node.func, ignore_exceptions,
                              catch_exception, depth],
                             [], *call_extra_parameters)

        return node

    def generic_visit(self, node):
        """Surround node statement with a try/except block to catch errors.

        This method is called for every node of the parsed code, and only
        changes statement lines.

        Args:
            node (ast.AST): node statement to surround.
        """
        if (isinstance(node, ast.stmt) and
                not isinstance(node, ast.FunctionDef)):

            new_node = self.wrap_with_try(node)

            # handling try except statement
            if isinstance(node, self.ast_try_except):
                self.try_except_handler(node)
                return new_node

            # Run recursively on all sub nodes
            super(ErrorsCatchTransformer, self).generic_visit(node)

            return new_node

        # Run recursively on all sub nodes
        return super(ErrorsCatchTransformer, self).generic_visit(node)


def get_last_lineno(node):
    """Recursively find the last line number of the ast node."""
    max_lineno = 0

    if hasattr(node, "lineno"):
        max_lineno = node.lineno

    for _, field in ast.iter_fields(node):
        if isinstance(field, list):
            for value in field:
                if isinstance(value, ast.AST):
                    max_lineno = max(max_lineno, get_last_lineno(value))

        elif isinstance(field, ast.AST):
            max_lineno = max(max_lineno, get_last_lineno(field))

    return max_lineno


def debug(victim, ignore_exceptions=(), catch_exception=None, depth=0):
    """A decorator function to catch exceptions and enter debug mode.

    Args:
        victim (typing.Union(type, function)): either a class or function to
            wrap and debug.
        ignore_exceptions (list): list of classes of exceptions not to catch.
        catch_exception (type): class of exception to catch and debug.
            default is None, meaning catch all exceptions.
        depth (number): how many levels of inner function calls to propagate.

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
            catch_exception=catch_exception,
            depth=depth)

        try:
            # Try to get the source code of the wrapped object.
            sourcelines, start_num = inspect.getsourcelines(victim.__code__)
            indent = re.match(r'\s*', sourcelines[0]).group()
            source = ''.join(l.replace(indent, '', 1) for l in sourcelines)

        except IOError:
            # Worst-case scenario we can only catch errors at a granularity
            # of the whole function
            return victim

        else:
            # If we have access to the source, we can silence errors on a
            # per-expression basis, which is "better"

            old_code_tree = ast.parse(source)
            # Reposition the line numbers to their original value
            ast.increment_lineno(old_code_tree, start_num - 1)
            tree = _transformer.visit(old_code_tree)

            import_debug_cmd = ast.ImportFrom(
                __name__, [ast.alias("start_debugging", None),
                           ast.alias("debug", None)], 0)

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

            # Add pass at the end (to enable debugging the last command)
            pass_cmd = ast.Pass()
            func_body = tree.body[0].body
            pass_cmd.lineno = get_last_lineno(func_body[-1]) + 1
            pass_cmd.col_offset = func_body[-1].col_offset
            func_body.append(pass_cmd)

            # Fix missing line numbers and column offsets before compiling
            for node in ast.walk(tree):
                if not hasattr(node, 'lineno'):
                    node.lineno = 0

            ast.fix_missing_locations(tree)

            # Define the wrapping function object
            function_definition = "def _free_vars_wrapper(): pass"
            wrapping_function = ast.parse(function_definition).body[0]

            # Initialize closure's variables to None
            body_list = [ast.parse("{var} = None".format(var=free_var)).body[0]
                         for free_var in victim.__code__.co_freevars]

            # Add the original function ("victim") to the wrapping function
            body_list.append(tree.body[0])

            wrapping_function.body = body_list

            # Replace original function ("victim") with the wrapping function
            tree.body[0] = wrapping_function

            # Create a new runnable code object to replace the original code
            code = compile(tree, victim.__code__.co_filename, 'exec')
            victim.__code__ = code.co_consts[0].co_consts[1]

            # Set a flag to indicate that the method was wrapped
            victim._ipdebug_wrapped = True

            return victim

    elif inspect.ismethod(victim):
        debug(victim.__func__, ignore_exceptions, catch_exception)
        return victim

    elif isinstance(victim, type):
        # Wrap each method of the class with the debugger
        for name, member in vars(victim).items():
            if isinstance(member, (type, types.FunctionType,
                                   types.LambdaType, types.MethodType)):
                setattr(victim, name,
                        debug(member, ignore_exceptions, catch_exception))

        return victim

    else:
        raise TypeError(
            "Debugger can only wrap functions and classes. "
            "Got object {!r} of type {}".format(victim, type(victim).__name__))
