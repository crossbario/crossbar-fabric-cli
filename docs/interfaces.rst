XBR Interfaces
==============

**cbsh** includes a Sphinx extension that allows to embed XBR IDL interface definition blocks in documentation markup (ReST).

Based on such markup, **cbsh** allows to:

1. render HTML documentation
2. extract XBR IDL definitions for loading into Crossbar.io


Usage
-----

Add the following to your Sphinx ``conf.py`` file:

.. code-block:: python

    extensions = [
        'sphinxcontrib.xbr',
    ]

Then declare **XBR namespaces** for subsequent interfaces (within the same document) like this:

.. code-block:: console

    .. xbr:namespace:: com.example.basic

.. xbr:namespace:: com.example.basic

This does not produce any HTML rendering output.

Then, define **XBR interfaces** like this:

.. code-block:: console

    .. xbr:interface:: IHello

        Hello world API. The most basic of all;)

        Services that implement :xbr:interface:`IHello` just expose one method
        that trivially returns a greeting message, and publishes an event.

        :version: 1
        :uuid: a7cbf72f44ec4ba38d2031f805f462d6

        .. xbr:procedure:: say_hello(name)

            Returns a hello message addressed to the given name.

            :param name: The name of the person to greet.
            :type name: str
            :returns: A greeting message.
            :rtype: str
            :raises: invalid_name

        .. xbr:event:: on_hello(msg)

            Event published when a hello message was sent.

            :param msg: The greeting message.
            :type msg: str

This renders in HTML to:

.. xbr:interface:: IHello

    Hello world API. The most basic of all;)

    Services that implement :xbr:interface:`IHello` just expose one method
    that trivially returns a greeting message, and publishes an event.

    :version: 1
    :uuid: a7cbf72f44ec4ba38d2031f805f462d6

    .. xbr:procedure:: say_hello(name)

        Returns a hello message addressed to the given name.

        :param name: The name of the person to greet.
        :type name: str
        :returns: A greeting message.
        :rtype: str
        :raises: invalid_name

    .. xbr:event:: on_hello(msg)

        Event published when a hello message was sent.

        :param msg: The greeting message.
        :type msg: str


You can then cross reference XBR interfaces in text like this :xbr:interface:`IHello` link which is rendered from:

.. code-block:: console

    :xbr:interface:`IHello`

