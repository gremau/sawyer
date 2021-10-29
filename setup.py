"""A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='sawyer',
    description='manage and quality-assure data from dataloggers and environmental sensor networks',
    long_description=long_description,
    version='2021.1b1',
    packages=find_packages(include=['sawyer', 'sawyer.*']),
    install_requires=[
        'ruamel_yaml',
        'pandas',
        'matplotlib']
    )
