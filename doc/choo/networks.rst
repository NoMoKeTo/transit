Network Reference
=================

.. py:class:: API

    The base class for all other APIs.

    .. py:method:: query(obj)

        Pass a Searchable and it will return a Searchable from the API or None/null if it could not be found. Pass a Searchable.Request and you will get a corresponding Searchable.Results.

.. py:class:: EFA

    Public transport API used world wide by many network operators.


Supported Networks
------------------

**VRR – Verkehrsverbund Rhein Ruhr** (``de.vrr`` :py:class:`EFA`)
    ifopt available. Also supports all of NRW and some parts of Germany.

**VRN – Verkehrsverbund Rhein-Neckar** (``de.vrn`` :py:class:`EFA`)
    ifopt available. Also supports some parts of Germany and Europe.
