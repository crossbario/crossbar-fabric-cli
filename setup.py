###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Crossbar.io Technologies GmbH
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
# THE SOFTWARE IS PROVIDED "AS IS", fWITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

from __future__ import absolute_import

from setuptools import setup, find_packages

with open('crossbarfabriccli/_version.py') as f:
    exec(f.read())  # defines __version__

with open('README.md') as f:
    docstr = f.read()

setup(
    name='crossbarfabriccli',
    version=__version__,
    description='Crossbar.io Fabric command line interface (CLI).',
    long_description=docstr,
    author='Crossbar.io Technologies GmbH',
    url='http://crossbario.com',
    platforms=('Any'),
    install_requires=[
        'autobahn[asyncio,accelerate,serialization,encryption]>=0.17.2',
        'click>=6.7',
        'prompt_toolkit>=1.0.13',
        'colorama>=0.3.7',
        'pygments>=2.2.0',
        'humanize>=0.5.1',
        'tabulate>=0.7.7',
        'pyyaml>=3.12'
    ],
    extras_require={
    },
    entry_points={
        'console_scripts': [
            'cbf = crossbarfabriccli.cli:main'
        ]
    },
    packages=find_packages(),
    include_package_data=True,
    data_files=[
        ('.', ['LICENSE', 'README.md'])
    ],
    zip_safe=False,
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=["License :: OSI Approved :: MIT License",
                 "Development Status :: 4 - Beta",
                 "Intended Audience :: Developers",
                 "Intended Audience :: System Administrators",
                 "Environment :: Console",
                 "Operating System :: OS Independent",
                 "Programming Language :: Python :: 3",
                 "Programming Language :: Python :: 3.5",
                 "Programming Language :: Python :: 3.6",
                 "Programming Language :: Python :: Implementation :: CPython",
                 "Programming Language :: Python :: Implementation :: PyPy"],
    keywords='crossbar.io crossbar wamp router cli administration management'
)
