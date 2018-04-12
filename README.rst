Crossbar.io Shell
=================

| |Version| |Build Status| |Coverage| |Docs|

--------------

Crossbar.io Shell (**cbsh**) is a tool belt for Crossbar.io featuring:

1. an **interactive shell** to access Crossbar.io Fabric Center and manage your Crossbar.io Fabric nodes from one central place and command line
2. a **service scaffolding** system that gets you started quickly using templates for Crossbar.io and Autobahn:

.. raw:: html

    <a href="https://asciinema.org/a/NMVxWjvqTrIN6l2bZDNTOLfLR" target="_blank"><img src="https://asciinema.org/a/NMVxWjvqTrIN6l2bZDNTOLfLR.png" /></a>

--------------

Installation
------------

Run this command to download the latest version of Crossbar.io Shell:

.. code-block:: console

    sudo curl -L https://s3.eu-central-1.amazonaws.com/download.crossbario.com/cbsh/linux/cbsh -o /usr/local/bin/cbsh

Apply executable permissions to the binary:

.. code-block:: console

    sudo chmod +x /usr/local/bin/cbsh

Test the installation:

.. code-block:: console

    oberstet@thinkpad-t430s:~$ which cbsh
    /usr/local/bin/cbsh
    oberstet@thinkpad-t430s:~$ cbsh version

    Crossbar.io Shell 18.4.5

    Platform                : Linux-4.4.0-119-generic-x86_64-with-glibc2.3.4
    Python (language)       : 3.6.5
    Python (implementation) : CPython
    Autobahn                : 18.4.1
    Docker Compose          : not installed
    Sphinx                  : 1.7.2
    Frozen executable       : yes
    Executable SHA256       : e45ecb24515b7a75521ecfb2084ca93745ca941e0b5146e0d0fe11b94834b85c

-------------

Documentation
-------------

Please refer to the `documentation <https://cbsh.readthedocs.io/en/latest/>`_ for description and usage **cbsh**.


.. |Version| image:: https://img.shields.io/pypi/v/cbsh.svg
   :target: https://pypi.python.org/pypi/cbsh

.. |Build Status| image:: https://travis-ci.org/crossbario/crossbar-shell.svg?branch=master
   :target: https://travis-ci.org/crossbario/crossbar-shell

.. |Coverage| image:: https://codecov.io/github/crossbario/crossbar-shell/coverage.svg?branch=master
   :target: https://codecov.io/github/crossbario/crossbar-shell

.. |Docs| image:: https://readthedocs.org/projects/crossbar-shell/badge/?version=latest
   :target: https://crossbar-shell.readthedocs.io/en/latest/
