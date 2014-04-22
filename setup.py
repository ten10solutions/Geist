#!/usr/bin/env python

from setuptools import setup
import os

with open(os.path.join('geist','version.py')) as f:
    exec(f.read())


setup(
    name='geist',
    version=__version__,
    packages=['geist', 'geist.backends'],
    install_requires=[
        'numpy>=1.7.0',
        'scipy',
        'ooxcb',
        'PyHamcrest',
        'pillow',
        'wrapt'
    ],
    description='Visual Automation Library',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
    ],
    license='MIT',
    author='The Test People Limited',
    maintainer='Tony Simpson',
    url='https://github.com/thetestpeople/Geist',
    test_suite="geist_tests",
)
