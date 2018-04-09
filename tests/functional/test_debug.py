"""Functional tests for the debug decorator in ipdbugger module."""
from __future__ import absolute_import
import sys
from unittest import TestCase, main

from IPython.utils.capture import capture_output

from ipdbugger import debug


try:
    from unittest.mock import patch

except ImportError:
    from mock import patch

TEST_FILE = "test_file.py"
PYTHON_PATH = sys.executable


class DebugCatchesExpcetionsCase(TestCase):
    """Tests that an exception is caught only iff one is raised."""

    @debug
    def shouldnt_raise(self):
        pass

    @debug
    def should_raise(self):
        raise Exception("Something bad happened")

    @patch('bdb.Bdb.set_trace')
    def test_should_raise(self, set_trace):
        with capture_output():
            self.should_raise()
            assert set_trace.called

    @patch('bdb.Bdb.set_trace')
    def test_shouldnt_raise(self, set_trace):
        with capture_output():
            self.shouldnt_raise()
            assert not set_trace.called


if __name__ == '__main__':
    main()
