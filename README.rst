Crossbar.io Fabric Shell
========================

Crossbar.io Fabric Shell (**cbsh**) is a tool belt for Crossbar.io featuring:

* an **interactive shell** to access Crossbar.io Fabric Center and manage your Crossbar.io Fabric nodes from one central place and command line
* a **service scaffolding** system that gets you started quickly using templates for Crossbar.io and Autobahn:

.. raw:: html

    <a href="https://asciinema.org/a/1XcqtsTSojDY6SS3R3bhI2WpB" target="_blank"><img src="https://asciinema.org/a/1XcqtsTSojDY6SS3R3bhI2WpB.png" /></a>

---------


Installation
------------

**cbsh** requires Python 3.5 or higher. Further, we strongly recommend installation into a dedicated virtual Python environment (see below).

The service scaffolding in addition requires:

* `Docker <https://docs.docker.com/install/>`_ and
* `Docker Compose <https://docs.docker.com/compose/install/>`_

To install **cbsh**, create a new dedicated virtual Python environment

.. code-block:: console

    python3 -m venv ~/cbsh
    source ~/cbsh/bin/activate

and install cbsh from `PyPi <https://pypi.org/project/cbsh/>`_ :

.. code-block:: console

    pip install cbsh

You can then check the path and version of **cbsh**:

.. code-block:: console

    (cbsh) oberstet@thinkpad-t430s:~$ which cbsh
    /home/oberstet/cbsh/bin/cbsh
    (cbsh) oberstet@thinkpad-t430s:~$ cbsh version
    Crossbar.io Fabric Shell 18.4.3

---------
