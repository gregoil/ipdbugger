"""Functional tests for the debug decorator in ipdbugger module."""
import os
import textwrap
from unittest import TestCase, main
from subprocess import Popen, PIPE


class ExceptionRaisedCase(TestCase):
    def test_method(self):
        # Create a python file that uses ipdbugger
        file_content = """
                     from ipdbugger import debug
                     @debug
                     def a():
                         raise NotImplementedError()
                     a()
                     """
        wrapped = textwrap.dedent(file_content)
        with open("test_file.py", "w") as test_file:
            test_file.write(wrapped)

        debugged = Popen(["python", "test_file.py"],
                         stderr=PIPE, stdin=PIPE, stdout=PIPE)
        stdout, stderr = debugged.communicate()
        self.assertIn(str.encode("Traceback"), stdout)

        # Remove the created python file
        os.remove("test_file.py")


class NoExceptionRaisedCase(TestCase):
    def test_method(self):
        # Create a python file that uses ipdbugger
        file_content = """
                     from ipdbugger import debug
                     @debug
                     def a():
                         pass
                     a()
                     """
        wrapped = textwrap.dedent(file_content)
        with open("test_file.py", "w") as test_file:
            test_file.write(wrapped)

        debugged = Popen(["python", "test_file.py"],
                         stderr=PIPE, stdin=PIPE, stdout=PIPE)
        stdout, stderr = debugged.communicate()
        self.assertNotIn(str.encode("Traceback"), stdout)

        # Remove the created python file
        os.remove("test_file.py")


if __name__ == '__main__':
    main()
