from setuptools import setup


packages = ['ipdbugger']

__version__ = "1.1.1"


setup(
    name='ipdbugger',
    version=__version__,
    install_requires=['ipdb',
                      'colorama',
                      'termcolor'],
    packages=packages,
    package_data={},
    zip_safe=False
)
