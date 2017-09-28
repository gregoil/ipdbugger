"""Setup file for handling packaging and distribution."""
from setuptools import setup

__version__ = "1.1.2"


setup(
    name='ipdbugger',
    version=__version__,
    install_requires=['ipdb',
                      'colorama',
                      'termcolor'],
    packages=['ipdbugger'],
    package_data={},
    zip_safe=False
)
