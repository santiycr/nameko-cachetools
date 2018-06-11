#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
doclink = """
Documentation
-------------

The full documentation is at http://nameko-cachetools.rtfd.org."""
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='nameko-cachetools',
    version='1.0.0',
    description=(
        'A few tools to cache interactions between your nameko services,'
        ' increasing resiliency and performance at the expense of consistency,'
        ' when it makes sense.'),
    long_description=readme + '\n\n' + doclink + '\n\n' + history,
    author='Santiago Suarez Ordonez',
    author_email='santiycr@gmail.com',
    url='https://github.com/santiycr/nameko-cachetools',
    packages=[
        'nameko_cachetools',
    ],
    package_dir={'nameko_cachetools': 'nameko_cachetools'},
    include_package_data=True,
    install_requires=[
        'nameko>=2.9.0',
    ],
    license='MIT',
    zip_safe=False,
    keywords='nameko-cachetools nameko cachetools cache rpc',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
