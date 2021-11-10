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
    description='Manage data workflows and build processing pipelines for data loggers and environmental sensor networks',
    long_description=long_description,
    version='2021.1b2',
    url='https://github.com/gremau/sawyer',  # Optional
    author='Gregory E. Maurer',  # Optional
    author_email='gmaurer@nmsu.edu',  # Optional
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=[
        'ruamel.yaml',
        'scipy',
        'pandas',
        'matplotlib']
    )
