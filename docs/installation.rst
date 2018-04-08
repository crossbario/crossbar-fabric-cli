Installation
============

**cbsh** requires Python 3.5 or higher. Further, we strongly recommend installation into a dedicated virtual Python environment (see below).

The service scaffolding in addition requires:

* `Docker <https://docs.docker.com/install/>`_
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
    Crossbar.io Shell 18.4.3
