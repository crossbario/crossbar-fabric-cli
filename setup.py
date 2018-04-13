#####################################################################################
#
#  Copyright (c) Crossbar.io Technologies GmbH
#
#  Unless a separate license agreement exists between you and Crossbar.io GmbH (e.g.
#  you have purchased a commercial license), the license terms below apply.
#
#  Should you enter into a separate license agreement after having received a copy of
#  this software, then the terms of such license agreement replace the terms below at
#  the time at which such license agreement becomes effective.
#
#  In case a separate license agreement ends, and such agreement ends without being
#  replaced by another separate license agreement, the license terms below apply
#  from the time at which said agreement ends.
#
#  LICENSE TERMS
#
#  This program is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License, version 3, as published by the
#  Free Software Foundation. This program is distributed in the hope that it will be
#  useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# 
#  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.en.html>.
#
#####################################################################################

from __future__ import absolute_import

from setuptools import setup

with open('cbsh/_version.py') as f:
    exec(f.read())  # defines __version__

with open('README.rst') as f:
    docstr = f.read()


setup(
    name='cbsh',
    version=__version__,  # noqa
    author='Crossbar.io Technologies GmbH',
    author_email='support@crossbario.com',
    description='Crossbar.io Shell (cbsh) is a tool belt for Crossbar.io',
    long_description=docstr,
    url='https://crossbario.com',
    platforms=('Any'),
    install_requires=[
        'autobahn[asyncio,serialization,encryption]>=18.4.1',   # MIT
        'click>=6.7',               # BSD
        'prompt_toolkit>=1.0.13',   # BSD
        'colorama>=0.3.7',          # BSD
        'pygments>=2.2.0',          # BSD
        'humanize>=0.5.1',          # MIT
        'tabulate>=0.7.7',          # MIT
        'pyyaml>=3.12',             # MIT
        'cookiecutter>=1.6.0',      # BSD
        'stringcase>=1.2.0',        # MIT
        'sphinx>=1.7.2',                    # BSD
        'sphinxcontrib-websupport>=1.0.1',  # BSD
        'sphinx_rtd_theme>=0.3.0',          # MIT
    ],
    extras_require={
    },
    entry_points={
        'console_scripts': [
            'cbsh = cbsh.cli:main'
        ]
    },
    # packages=find_packages(),
    packages=[
        'cbsh',
        'sphinxcontrib.xbr'
    ],    
    include_package_data=True,
    data_files=[
        ('.', ['LICENSE', 'README.rst'])
    ],
    zip_safe=True,
    license='MIT License',
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
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
