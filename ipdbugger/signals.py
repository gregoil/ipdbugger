"""Signals usage in Rotest."""
# pylint: disable=global-statement,no-member
import sys
import signal


BREAKPOINT_SIGNAL_REGISTERED = False


class BreakPointException(Exception):
    """An exception to raise on the break signal."""


def raise_exception_handler(_signum, _frame):
    """Raise a break-point exception."""
    raise BreakPointException()


def register_break_signal():
    """Register raising an exception on break signal if needed."""
    global BREAKPOINT_SIGNAL_REGISTERED
    if BREAKPOINT_SIGNAL_REGISTERED:
        return

    BREAKPOINT_SIGNAL_REGISTERED = True

    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, raise_exception_handler)

    else:
        signal.signal(signal.SIGQUIT, raise_exception_handler)
