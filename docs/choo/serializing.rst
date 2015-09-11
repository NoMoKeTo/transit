Model Serialization / JSON
==========================

All choo models can be (un)serialized to/from a JSON-encodable format.

In Python
---------

.. code-block:: python

    from models import Stop, Location, Serializable
    # Create a Stop
    stop = Stop(city='Essen', name='Hauptbahnhof')

    # serialization
    serialized = stop.serialize()

    # unserialize
    stop = Stop.unserialize(serialized)
    stop = Location.serialize(serialized)  # same result
    stop = Serializable.serialize(serialized)  # same result

    # this will fail because Stop is not a submodel of Ride
    stop = Ride.serialize(serialized)


How it works
------------

.. _`Model Reference`: models.html

.. caution::
    Some models have a non-dictionary representation or some additional attributes in their dictionary representation. See the `Model Reference`_ for more information.

All public attributes that are not dynamic and not ``None`` are put into a dictionary. All values are serialized.

| **datetime** values are respresented as a string in ``YYYY-MM-DD HH:II:SS`` format.
| **timedelta** values are respresented as a the total number of seconds as int.

.. code-block:: json

    {
        "type": "Stop",
        "_ids": {"vrr": 20009289},
        "country": "de",
        "city": "Essen",
        "name": "Hauptbahnhof",
        "coords": [51.451139, 7.012937]
    }
