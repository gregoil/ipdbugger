"""Setup file for handling packaging and distribution."""
import sys

from setuptools import setup

__version__ = "2.0.0"

REQUIREMENTS = [
    "ipdb",
    "colorama",
    "termcolor",
    "ipython{}".format(
        "<6.0.0" if sys.version < "3.4" else "")
]

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
    install_requires=REQUIREMENTS,
    packages=["ipdbugger"],
    python_requires=">=2.7",
    package_data={'': ['*.xls', '*.xsd', '*.json',
                       '*.css', '*.xml', '*.rst']},
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6'
    ],
    zip_safe=False,
)
