"""Setup file for handling packaging and distribution."""
from setuptools import setup

__version__ = "2.0.1"

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
                      "future",
                      "colorama",
                      "termcolor"],
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
    zip_safe=False
)
