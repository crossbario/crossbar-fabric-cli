###############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) Crossbar.io Technologies GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', fWITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

from __future__ import absolute_import

from setuptools import setup

with open('cbsh/_version.py') as f:
    exec(f.read())  # defines __version__

with open('README.rst') as f:
    docstr = f.read()


setup(
    name='cbsh',
    version=__version__,  # noqa
    description='Crossbar.io Shell (cbsh) is a tool belt for Crossbar.io',
    long_description=docstr,
    author='Crossbar.io Technologies GmbH',
    url='https://crossbario.com',
    platforms=('Any'),
    install_requires=[
        'autobahn[asyncio,serialization,encryption]>=18.3.1',   # MIT
        'click>=6.7',               # BSD
        'prompt_toolkit>=1.0.13',   # BSD
        'colorama>=0.3.7',          # BSD
        'pygments>=2.2.0',          # BSD
        'humanize>=0.5.1',          # MIT
        'tabulate>=0.7.7',          # MIT
        'pyyaml>=3.12',             # MIT
        'cookiecutter>=1.6.0',      # BSD
        'sphinx>=1.7.2',            # BSD
        'sphinx_rtd_theme>=0.3.0',  # MIT
        'stringcase>=1.2.0',        # MIT
    ],
    extras_require={
    },
    entry_points={
        'console_scripts': [
            'cbsh = cbsh.cli:main'
        ]
    },
    packages=[
        'cbsh',
        'sphinxcontrib'
    ],
    include_package_data=True,
    data_files=[
        ('.', ['LICENSE', 'README.rst'])
    ],
    zip_safe=False,
    license='MIT License',
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Framework :: Sphinx :: Extension',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Documentation :: Sphinx',
        'Topic :: Software Development :: Documentation',
    ],
    keywords='crossbar xbr autobahn wamp idl router cli administration'
)
