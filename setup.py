#!/usr/bin/env python2

import os
import string
import subprocess
import warnings

#from distutils.core import setup
from setuptools import setup

MAJOR = 0
MINOR = 1
PATCH = 0

RELEASE = False

VERSION = "{0}.{1}.{2}".format(MAJOR, MINOR, PATCH)

if not RELEASE:
    try:
        try:
            pipe = subprocess.Popen(["git", "describe", "--dirty", "--tags"],
                                    stdout=subprocess.PIPE)
        except EnvironmentError:
            warnings.warn("WARNING: git not installed or failed to run")

        revision = pipe.communicate()[0].strip().lstrip('v')
        if pipe.returncode != 0:
            warnings.warn("WARNING: couldn't get git revision")

        if revision != VERSION:
            revision = revision.lstrip(string.digits + '.')
            VERSION += '.dev' + revision
    except:
        VERSION += '.dev'
        warnings.warn("WARNING: git not installed or failed to run")


def write_version():
    """writes the leif/version.py file"""
    template = """\
__version__ = '{0}'
"""
    filename = os.path.join(
        os.path.dirname(__file__), 'leif', 'version.py')
    with open(filename, 'w') as versionfile:
        versionfile.write(template.format(VERSION))
        print("wrote leif/version.py with version={0}".format(VERSION))

write_version()


requirements = [
    'lxml',
    'requests',
]

setup(
    name='leif',
    version=VERSION,
    description='A CalDav and CardDAV auto discovery library and tool',
    long_description=open('README.rst').read(),
    author='Christian Geier',
    author_email='khal@lostpackets.de',
    url='http://github.com/geier/leif/',
    license='Expat/MIT',
    packages=['leif'],
    #scripts=['bin/leif'],   # TODO factor tool into seperate script
    requires=requirements,
    classifiers=[
        "Development Status :: 1 - Planning"
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2 :: Only",
        "Topic :: Utilities",
    ],
)
