###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Tavendo GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

from __future__ import absolute_import

import sys
import re
import os
import platform
from setuptools import setup, find_packages

# Get package version and docstring from cdc/__init__.py
#
PACKAGE_FILE = "crossbar-fabric-cli/__init__.py"
initfile = open(PACKAGE_FILE, "rt").read()

VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, initfile, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in {}.".format(PACKAGE_FILE))

DSRE = r"__doc__ = \"\"\"(.*)\"\"\""
mo = re.search(DSRE, initfile, re.DOTALL)
if mo:
    docstr = mo.group(1)
else:
    raise RuntimeError("Unable to find doc string in {}.".format(PACKAGE_FILE))


setup(
    name='crossbar-fabric-cli',
    version=verstr,
    description='Crossbar.io Fabric command line interface (CLI).',
    long_description=docstr,
    author='Tavendo GmbH',
    author_email='autobahnws@googlegroups.com',
    url='http://crossbar.io/',
    platforms=('Any'),
    install_requires=[
        'autobahn[asyncio]>=0.10.5',  # MIT license
        'humanize>=0.5.1',            # MIT license
    ],
    extras_require={
    },
    entry_points={
        'console_scripts': [
            'cfb = crossbar-fabric-cli.main:cdc'
        ]},
    packages=find_packages(),
    include_package_data=True,
    data_files=[('.', ['LICENSE', 'README.md'])],
    zip_safe=False,
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    #
    classifiers=["License :: OSI Approved :: MIT License",
                 "Development Status :: 4 - Beta",
                 "Intended Audience :: Developers",
                 "Intended Audience :: System Administrators",
                 "Environment :: Console",
                 "Operating System :: OS Independent",
                 "Programming Language :: Python :: 2.6",
                 "Programming Language :: Python :: 2.7",
                 "Programming Language :: Python :: 3",
                 "Programming Language :: Python :: 3.3",
                 "Programming Language :: Python :: 3.4",
                 "Programming Language :: Python :: Implementation :: CPython",
                 "Programming Language :: Python :: Implementation :: PyPy"],
    keywords='crossbar.io crossbar'
)
