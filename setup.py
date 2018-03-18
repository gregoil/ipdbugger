"""Setup file for handling packaging and distribution."""
from setuptools import setup

__version__ = "1.1.3"


setup(
    name="ipdbugger",
    version=__version__,
    description="ipdb-based debugger",
    long_description=open("README.rst").read(),
    license="MIT",
    author="gregoil",
    author_email="gregoil@walla.co.il",
    url="https://github.com/gregoil/ipdbugger",
    keywords="ipdb debug debugger exception",
    install_requires=["ipdb",
                      "colorama",
                      "termcolor"],
    packages=["ipdbugger"],
    package_data={'': ['*.xls', '*.xsd', '*.json', '*.css', '*.xml', '*.rst']},
    zip_safe=False
)
