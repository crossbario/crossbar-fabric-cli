Crossbar.io Shell
=================

| |Version| |Travis| |Appveyor|  |Coverage| |Docs|

--------------

Crossbar.io Shell (**cbsh**) is a tool belt for Crossbar.io featuring:

1. an **interactive shell** to access Crossbar.io Fabric Center and manage your Crossbar.io Fabric nodes from one central place and command line
2. a **service scaffolding** system that gets you started quickly using templates for Crossbar.io and Autobahn:

.. raw:: html

    <a href="https://asciinema.org/a/NMVxWjvqTrIN6l2bZDNTOLfLR" target="_blank"><img src="https://asciinema.org/a/NMVxWjvqTrIN6l2bZDNTOLfLR.png" /></a>

--------------

Installation
------------

Linux
.....

For Linux (64-bit), we provide `cbsh` as a one-file executable that is completely
statically linked and should run on basically any Linux distribution.

Run this command to download the latest version of the Crossbar.io Shell executable
and install to ``/usr/local/bin``:

.. code-block:: console

    sudo curl -L https://s3.eu-central-1.amazonaws.com/download.crossbario.com/cbsh/linux/cbsh -o /usr/local/bin/cbsh

Apply executable permissions to the binary:

.. code-block:: console

    sudo chmod +x /usr/local/bin/cbsh

Test the installed binary:

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

As the installation path ``/usr/local/bin`` is in the search PATH of most Linux systems by default,
**cbsh** will be automatically available *for all users* on the system.

To update **cbsh** at a later time, just download the new version by rerunning above ``curl`` command.

-------------


Other OS
........

**cbsh** should run on any system with a recent Python 3, and we publish releases on PyPI.

We recommend installation into a dedicated Python virtual environment:

.. code-block:: console

    python3 -m venv cbsh
    cbsh/bin/pip3 install --no-cache cbsh

.. note::

    To install a specific version, use eg ``cbsh==18.4.1`` in above last command.

To check the installation:

.. code-block:: console

    oberstet@thinkpad-t430s:~$ cbsh/bin/cbsh version

    Crossbar.io Shell 18.4.6-dev2

    Platform                : Linux-4.4.0-119-generic-x86_64-with-glibc2.9
    Python (language)       : 3.5.2
    Python (implementation) : CPython
    Autobahn                : 18.4.1
    Docker Compose          : 1.21.0
    Sphinx                  : 1.7.2
    Frozen executable       : no

You can also activate the Python virtual environment by doing (on Unix):

    source cbsh/bin/activate

This will make the Python of the virtual environment, and the **cbsh**
installed therein available without qualifying paths - in the current
terminal session.

Finally, you can add the directory path ``cbsh/bin/`` to your environment search PATH,
eg on Unix systems by ``export PATH=${HOME}/cbsh/bin:${PATH}``. That will make **cbsh**
available in terminal sessions automtically.

To update **cbsh** at a later time, run:

.. code-block:: console

    cbsh/bin/pip3 install --no-cache --upgrade cbsh

-------------



Requires Microsoft Windows 10 Professional or Enterprise 64-bit 
https://www.docker.com/docker-windows
https://store.docker.com/editions/community/docker-ce-desktop-windows



Get Docker Community Edition for Windows

Docker for Windows is available for free.

Requires Microsoft Windows 10 Professional or Enterprise 64-bit. For previous versions get Docker Toolbox.
By downloading this, you agree to the terms of the Docker Software End User License Agreement




Documentation
-------------

Please refer to the `documentation <https://cbsh.readthedocs.io/en/latest/>`_ for description and usage **cbsh**.


.. |Version| image:: https://img.shields.io/pypi/v/cbsh.svg
   :target: https://pypi.python.org/pypi/cbsh

.. |Travis| image:: https://travis-ci.org/crossbario/crossbar-shell.svg?branch=master
   :target: https://travis-ci.org/crossbario/crossbar-shell

.. |Appveyor| image:: https://ci.appveyor.com/api/projects/status/github/crossbario/crossbar-shell?branch=master&svg=true
    :target: https://ci.appveyor.com/project/crossbar/crossbar-shell

.. |Coverage| image:: https://codecov.io/github/crossbario/crossbar-shell/coverage.svg?branch=master
   :target: https://codecov.io/github/crossbario/crossbar-shell

.. |Docs| image:: https://readthedocs.org/projects/crossbar-shell/badge/?version=latest
   :target: https://crossbar-shell.readthedocs.io/en/latest/
