Getting Started
===============

The Choo Data Model
----------------------

Before we start using choo, you have to understand its underlying Models.

**Stop**
    A Stop is a group of Platforms (e.g. Berlin Hbf).

**Platform**
    A Platform is a place where rides stop (e.g. Gleis 7). It belongs to one Stop.

**Ride**
    A Ride is the journey of a bus/train/etc. It only happens once. Even the “same” ride on the next day is handled as another Ride.

**Line**
    A Line is a name for a group of Rides (e.g. Bus Line 495). Every Ride belongs to one Line.

**Trip**
    A Trip is a connection between two Stops (or GeoLocations to be precise, see below) with rides, interchanges and/or footpaths in between.

The models **Stop**, **Adress** and **POI** (Point of Interest) are all subclasses of **Location** which describes a stand-alone Location with City and Name

Also, **Location** and **Platform** are subclasses of **GeoLocation** which describes anything that has a static position.

Those models are called **Searchables** because you can search for them with choo. You can...

* provide an instance of them. choo will try to retrieve it and return a more complete version of it to you
* use their ``Request`` submodel to specify what you are looking. choo will use the ``Result`` submodel to give you the search results.

Some other Models that are part of choo but can not be searched for:

**Way**
    A path between two GeoLocation objects.

**RidePoint**
    A time and place object describes the time, stop and platform and coordinates where a ride meets a stop.

**RideSegment**
    In most cases, we are only interested in a part of a Ride – from where you enter the train/bus/etc. to where you leave it.
    That part is called a RideSegment – it consists of a Ride and the start and end point of the segment.

**LiveTime**
    Points in time are always given as a LiveTime object, which consists of a datetime and a delay (if known).

**WayType**
    Each Way has a waytype. A WayType has one of the values ``walk``, ``bike``, ``car`` or ``taxi``

**LineType**
    Each Line has a linetype. A Linetype has one of the values ``(empty string)``, ``train``, ``train.local``, ``train.longdistance``, ``train.longdistance.highspeed``,
    ``urban``, ``metro``, ``tram``, ``bus``, ``bus.regional``, ``bus.city``, ``bus.express``, ``suspended``, ``ship``, ``dialable``, or ``other``.

    An empty string means that it can be anyone of the other linetypes, The linetype ``bus`` means that it could be any of the bus-subtypes. The reason for this is that
    not all networks differentiate between some subtyes (e.g. bus types). See the network reference for which linetypes it may output.

For more information, see `Model Reference`_.


Command Line Interface
----------------------

.. code-block:: none

    usage: choo [-h] [--pretty] network query

    positional arguments:
      network     network to use, e.g. vrr
      query       any Searchable or Searchable.Request as JSON

    optional arguments:
      -h, --help  show this help message and exit
      --pretty    pretty-print output JSON


To get startet, let's look up Essen Hauptbahnhof in the VRR network using the command line interface.

To do so, we first have to describe Essen Hauptbahnhof as a ``Stop``:

.. code-block:: json

    ["Stop", {
      "name": "Essen Hauptbahnhof"
    }]

Now we pass this data to the API. We use the network ``vrr``. ``--pretty`` means that the resulting JSON should be pretty printed.

.. code-block:: none

    $ choo --pretty vrr '["Stop", {"name": "Essen Hauptbahnhof"}]'

We get the following result:

.. code-block:: json

    [
      "Stop",
      {
        "id": 20009289,
        "source": "vrr",
        "coords": [
          51.451137,
          7.012941
        ],
        "country": "de",
        "city": "Essen",
        "name": "Hauptbahnhof",
        "full_name": "Essen Hbf",
        "ifopt": "de:5113:9289",
        "rides": {  },
        "lines": {  }
      }
    ]

As you can see, the API returned a Stop with more information.

The stop now is defined by it’s correct country, city, name and full_name attribute. Also, we have its coordinates now. ``source`` contains the name of the network that gave us this data. ``id`` is the ID of the Stop in this network.

The ``rides`` and ``lines`` attributes were shortened in this example but will give you ``Ride.Results`` and ``Line.Results`` if the API provides this information. If not, you can still use a ``Ride.Request`` oder ``Line.Request`` to request it explicitely.

For more information about the JSON format, see `Model Reference`_ and `Model Serialization`_.

For more information about how to query information, see `Network API`_.

.. _`Network API`: networks.html
.. _`Model Reference`: models.html
.. _`Model Serialization`: serializing.html

Python Interface
----------------

Let's see how you would access this via the Python interface.

.. code-block:: python

    from choo.models import Stop
    from choo.networks.de import vrr

    essen = Stop(name='Essen Hauptbahnhof')
    essen = vrr.query(essen)

We created the Stop, got the network and used the generic .query() function of the VRR api wich gave us the same result as above.

.. code-block:: python

    print(essen.city)  # Essen
    print(essen.name)  # Hauptbahnhof
    print(essen.full_name)  # Essen Hbf

    # iterates through all lines
    for line in essen.lines:
        print(line.shortname)  # RB40 and similar

    # iterates through all rides
    for ridesegment in essen.rides:
        ride = ridesegment.ride

        print(ride.number)  # train number or similar
        print(ride.line.shortname)  # 106 or similar

        # all Ride attributes can also accessed using the RideSegment
        print(ridesegment.number)  # same as ride.number

        # iterate through all stops of the RideSegment
        for ridepoint in ridesegment:
            if ridepoint is not None:  # this is not a gap
                if ridepoint.departure is not None:  # we now the departure
                    print(ridepoint.departure.time)  # planned time as datetime.datetime
                    print(ridepoint.departure.delay)  # expceted delay as datetime.datetimeplanned time as datetime.datetime
                    print(ridepoint.departure.is_live)  # shortcut for delay is not None
                    print(ridepoint.departure.expected_time)  # expceted time if real time information is available, otherwise planned time
                print(ridepoint.stop.name) # Hauptbahnhof or similar

        # iterate through all stops of the Ride
        for ridepoint in ridesegment.ride:
            # same as above, but without boundaries

        # you can also slice a ride or ride segment to get another ride segment
        newsegment = ridesegment.ride[1:]

For more information, see `Model Reference`_.


HTTP API
--------

.. code-block:: none

    usage: choo-server [-h] [--host HOST] [--port PORT]

    optional arguments:
      -h, --help   show this help message and exit
      --host HOST  set address to listen on (default: 0.0.0.0)
      --port PORT  set tcp port (default: random unused port)

Just start it and open it in your browser to see the API.


How to search for a Trip
------------------------

Just query the Request-submodel of Trip, like explained above. Simple example:

.. code-block:: json

    ["Trip.Request", {
        "origin:" ["Stop", {
            "name": "Essen Hauptbahnhof"
        }],
        "destination:" ["Stop", {
            "name": "Dortmund Hauptbahnhof"
        }]
    }]

.. code-block:: python

    Trip.Request(origin=Stop(name='Essen Hauptbahnhof'),
                 destination=Stop(name='Dortmund Hauptbahnhof'))
