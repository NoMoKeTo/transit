Model Reference
===============

.. note::
    Every attribute can be None when no data is available, unless noted otherwise.

Base Models
-----------

All choo models are based upon one of the following three base classes that build on top of each other.

.. py:class:: Serializable

    All models are Serializables. See `Model Serialization`_ for more information.

    .. method:: validate()

        Checks if all attributes have valid values. Raises an exception if the object is not valid. This method is also called by ``serialize()``.

    .. method:: serialize()

        Serializes this object in a JSON-encodable format. This is a shortcut for Serializable.serialize(serializable).

        :rtype: the serialized object

    .. classmethod:: serialize(obj)

        Serializes the given instance of this model in a JSON-encodable format, using typed serialization if the given object is an instance of a submodel.

        .. code-block:: python

            >>> stop.serialize()
            {…}
            >>> Stop.serialize(stop) == stop.serialize()
            True
            >>> Location.serialize(stop)
            ['Stop', {…}]
            >>> Location.serialize(stop)[1] == stop.serialize()
            True

        :param obj: A serialized representation of a choo object
        :rtype: the serialized object

    .. classmethod:: unserialize(data)

        Unserializes an object of this model or one of its child classes from a JSON-encodable format. Always use the same model for unserialization as you used for serialization.

        :param data: A serialized representation of an object of this model or one of its submodels.
        :rtype: the unserialized object

.. _`Model Serialization`: serializing.html


.. py:class:: Searchable

    An :py:class:`Serializable` that can be searched for. You can pass it to the API and to get its complete information.

    All subclasses have a ``Request`` and a ``Results`` subclass. You can pass the and instance of the Request subclass to the API to get search results in a Results subclass.

    .. py:class:: Searchable.Request(Serializable)

        A request template for this Model with lots of possible search criteria that can be set.

    .. py:class:: Searchable.Results(Serializable)

        A list (of Request-Results) of instances of this object. Those lists can have match scores.

        You can just iterate over this object to get its contents.

        .. method:: scored(obj)

            Returns an iterator over tuples of (results, score).

        .. method:: filter(request)

            Remove all objects that do not match the given Request.

        .. method:: filtered(request)

            Returns a new ``Results`` instance with all objects that do not match the given Request removed.

        .. note::
            For serialization, the list of results is stored in the property ``results`` as a list. Each element of this list is a two-element list containing the serialized result and the match score.

            Please note that the serialized result is typed serialized if the Model has submodels (e.g. :py:class:`Location`, which has :py:class:`Stop` etc…)


.. py:class:: Collectable

    A :py:class:`Searchable` that can be collected. It has an ID and it really exists and is not some kind of data construct.

    .. py:attribute:: source

        Source Network of this object. All APIs set this attribute, but it is not mandatory for input.

    .. py:attribute:: id

        ID of this object (as ``str``) in the source network.


GeoLocation
-----------

.. py:class:: GeoLocation

    *Submodel of :py:class:`Serializable`.*

    Abstract base class for everything that has a fixed position.

    .. attribute:: lat

        latitude as float

    .. attribute:: lon

        longitude as float


Coordinates
-----------

.. py:class:: Coordinates(lat, lon)

    *Submodel of :py:class:`GeoLocation`.*

    A Model just geographic coordinate.

    You can cast :py:class:`Coordinates` to tuple if needed:

    .. code-block:: python

        >>> tuple(Coordinates(51.445555, 7.017253))
        (51.445555, 7.017253)


Platform
--------

.. py:class:: Platform(stop, name=None, full_name=None)

    *Submodel of :py:class:`Collectable` and :py:class:`GeoLocation`.*

    An place where rides stop (e.g. Gleis 7). It belongs to one :py:class:`Stop`.

    .. attribute:: ifopt

        The globally unique ID of this Platform according to *Identification of Fixed Objects in Public Transport* supported by some APIs.

    .. attribute:: stop

        **Not None.** The :py:class:`Stop` this platform belongs to.

    .. attribute:: name

        The name of this Platform (e.g. 7 or 2b).

    .. attribute:: full_name

        The full name of this Platform (e.g. Bussteig 7 or Gleis 2b)

    .. py:class:: Platform.Request

        Submodel of :py:class:`Searchable.Request`.

    .. py:class:: Platform.Results

        Submodel of :py:class:`Searchable.Results`.


Location
--------

.. py:class:: Location(country=None, city=None, name=None)

    *Submodel of :py:class:`Collectable` and :py:class:`GeoLocation`.*

    Abstract base class place that is named and not a sublocation like a :py:class:`Platform`.

    .. attribute:: country

        The country of this location as a two-letter country code.

    .. attribute:: city

        The name of the city this location is located in.

    .. attribute:: name

        The name of this location. If the ``city`` attribute is ``None`` this it may also included in the name.

    .. attribute:: near_stops

        Other stops near this one as a ``Stop.Results``, if available. You can always search for Stops near a :py:class:`GeoLocation` directly using ``Stop.Request``.

    .. py:class:: Location.Request

        Submodel of :py:class:`Searchable.Request`.

        .. attribute:: name

            A search string for the name of the Location.

        .. attribute:: city

            City of the Location.

    .. py:class:: Location.Results

        Submodel of :py:class:`Searchable.Results`.

Stop
----

.. py:class:: Stop(country=None, city=None, name=None)

    *Submodel of :py:class:`Location`.*

    A train station, bus stop, etc. For example: Düsseldorf Hbf.

    .. attribute:: ifopt

        The globally unique ID of this Stop according to *Identification of Fixed Objects in Public Transport* supported by some APIs.

    .. attribute:: uic

        The is the international train station id by the *International Union of Railways*.

    .. attribute:: full_name

        The full name of this Stop. Can be just the city and the name, but does'nt have to.

    .. attribute:: lines

         The Lines that are available at this stop as a ``Line.Results`` object, if available. You can always search for Lines at a :py:class:`Stop` using :py:class:`Line.Request`.

    .. attribute:: rides

        The next rides at this stop as a ``Ride.Results`` object, if available. You can always search for Rides at a :py:class:`Stop` using :py:class:`Ride.Request`.

    .. py:class:: Stop.Request

        Submodel of :py:class:`Location.Request`.

    .. py:class:: Stop.Results

        Submodel of :py:class:`Location.Results`.


Address
-------

.. py:class:: Address(country=None, city=None, name=None)

    *Submodel of :py:class:`Location`.*

    An address. The ``name`` attribute contains the address in one string, but more detailed attributes may be available:

    .. attribute:: street

        The name of the street.

    .. attribute:: number

        The house number as a string.

    .. py:class:: Address.Request

        Submodel of :py:class:`Location.Request`.

    .. py:class:: Address.Results

        Submodel of :py:class:`Location.Results`.


POI
---

.. py:class:: POI(country=None, city=None, name=None)

    *Submodel of :py:class:`Location`.*

    A Point of Interest.

    .. py:class:: POI.Request

        Submodel of :py:class:`Location.Request`.

    .. py:class:: POI.Results

        Submodel of :py:class:`Location.Results`.


Ride
----

.. py:class:: Ride(line=None, number=None)

    *Submodel of :py:class:`Collectable`.*

    A ride is implemented as a list of :py:class:`RidePoint` objects and suppors nearly all methods of Python's native ``list`` type.

    If you iterate over a :py:class:`Ride` each item you get is ``None`` or a :py:class:`RidePoint` object. Each item that is ``None`` stands for n missing stations. It can also mean that the :py:class:`RidePoint` before and after the item are in fact the same. To get rid of all ``None`` items, pass an incomplete ride to a network API.

    You can slice a :py:class:`Ride` which will get you a :py:class:`RideSegment` that refers to the original ride but always will have the correct boundaries, even if elements between are removed or inserted between them. Slicing with no start or no end point is also supported.

    .. caution::
        Slicing a :py:class:`Ride` is inclusive! For example, slicing from element 2 to element 5 results in a :py:class:`RideSegment` describing the journey between element 2 and element 5, containing 4 elements in total!

    .. attribute:: time
        The time at which the ride data was retrieved as ``datetime``.

    .. attribute:: line

        **Not None.** The :py:class:`Line` of this :py:class:`Ride`.

    .. attribute:: number

        The number (train number or similar) of this :py:class:`Ride` as a string.

    .. attribute:: canceled

        A boolean indicating whether this ride has been canceled.

    .. attribute:: bike_friendly

        A boolean indicating whether this is a bike-friendly vehicle.

    .. method:: append(item)

        Append a :py:class:`RidePoint` object (or None).

    .. method:: prepend(item)

        Prepend a :py:class:`RidePoint` object (or None).

    .. method:: insert(position, item)

        Insert a :py:class:`RidePoint` (or None) as the new position ``position``.

    .. method:: remove(item)

        Remove this :py:class:`RidePoint` (not None) from the list.

    .. method:: pop([i])

        Remove the item at the given position (default: last position) from the list.

    .. method:: index([i])

        Remove the item at the given position (default: last position) from the list.

    You can also use ``in`` and ``del``.

    .. attention::
        The following attributes are **dynamic** and can not be set.

    .. attribute:: path
        Get the geographic path of the ride as a list of :py:class:`Coordinates`. If you only want to get the path between to stops, just use the :py:class:`RideSegment` property with the same name.

        Falls back to just directly connecting the platform or stop coordinates if no other information is available.

    .. note::
        For serialization, the property ``stops`` is created containing a list of the serialized elements. Each :py:class:`RidePoint` element can have the additional property ``path_to_next`` containing a list of tupled py:class:`Coordinates`.

    .. py:class:: Ride.Request

        Submodel of :py:class:`Searchable.Request`.

    .. py:class:: Ride.Results

        Submodel of :py:class:`Searchable.Results`.


RideSegment
-----------

.. py:class:: RideSegment
    *Submodel of :py:class:`TripPart`.*

    This class created by slicing :py:class:`Ride` objects.

    This model is usable in the same way as a :py:class:`Ride`. Slicing it will return another :py:class:`RideSegment` for the same :py:class:`Ride`.

    .. caution::
        Slicing a :py:class:`Ride` is inclusive! For example, slicing from element 2 to element 5 results in a :py:class:`RideSegment` describing the journey between element 2 and element 5, containing 4 elements in total!

    .. attribute:: ride

        **Not None.** The :py:class:`Ride` that this object is a segment of.

    .. method:: index([i])

        Remove the item at the given position (default: last position) from the list.

    You can also use ``in``.

    .. attention::
        The following attributes are **dynamic** and can not be set.

    .. attribute:: path
        Get the geographic path of the ride segment as a list of :py:class:`Coordinates`.

        Falls back to just directly connecting the platform or stop coordinates if no other information is available.

    .. attribute:: origin

        The first :py:class:`Stop` of this segment. Shortcut for ``segment[0].stop``.

    .. attribute:: destination

        The last :py:class:`Stop` of this segment. Shortcut for ``segment[-1].stop``.

    .. attribute:: departure

        The departure at the first :py:class:`Stop` of this segment as :py:class:`LiveTime`. Shortcut for ``segment[0].departure``.

    .. attribute:: arrival

        The arrival at the last :py:class:`Stop` of this segment as :py:class:`LiveTime`. Shortcut for ``segment[-1].arrival``.

    .. note::
        For serialization, the boundaries are given as integer indexes as properties ``origin`` and ``destination``. Each one can be missing if the boundary is not set. (e.g. ``ride[5:]``)

        Don't forget that Ride slicing is inclusive (see above)!


RidePoint
---------

.. py:class:: RidePoint(platform, arrival=None, departure=None)

    *Submodel of :py:class:`Serializable`.*

    Time and place of a :py:class:`Ride` stopping at a :py:class:`Platform`.

    .. attribute:: platform

        **Not None.** The :py:class:`Platform`.

    .. attribute:: arrival

        The arrival time of the :py:class:`Ride` as :py:class:`LiveTime`.

    .. attribute:: departure

        The departure time of the :py:class:`Ride` as :py:class:`LiveTime`.

    .. attribute:: passthrough

        A boolean indicating whether the ride does not actually stop at this :py:class:`Stop` but pass through it.


LiveTime
--------

.. py:class:: LiveTime(time, delay=None)

    *Submodel of :py:class:`Serializable`.*

    A point in time with optional real time data.

    :param time: The originally planned time as a `datetime.datetime` object.
    :param delay: The (expected) delay as a `datetime.timedelta` object if known.

    .. attribute:: time

        **Not None.** The originally planned time as a `datetime.datetime` object.

    .. attribute:: delay

        The (expected) delay as a `datetime.timedelta` object or None.
        Please note that a zero delay is not the same as None. None stands for absence of real time information.

    .. attention::
        The following attributes are **dynamic** and can not be set.

    .. attribute:: is_live

        True if there is real time data available. Shortcut for ``delay is not None``

    .. attribute:: expected_time

        The (expected) actual time as a `datetime.datetime` object if real time data is available, otherwise the originally planned time.


Line
----

.. py:class:: Line(linetype=None)

    *Submodel of :py:class:`Collectable`.*

    A group of Rides (e.g. Bus Line 495). Every :py:class:`Ride` belongs to one Line.

    .. attribute:: linetype

        **Not None.** The :py:class:`LineType` of this :py:class:`Line`.

    .. attribute:: product

        The product name, for example `InterCity`, `Hamburg-Köln-Express` or `Niederflurbus`.

    .. attribute:: name

        **Not None** The long name of the :py:class:`Line`, for example `Rhein-Haardt-Express RE2`.

    .. attribute:: shortname

        **Not None** The short name of the :py:class:`Line`, for example `RE2`.

    .. attribute:: route

        The route description.

    .. attribute:: first_stop

        The first :py:class:`Stop` of this :py:class:`Line`. Rides may start at a later station.

    .. attribute:: last_stop

        The last :py:class:`Stop` of this :py:class:`Line`. Rides may end at a earlier station.

    .. attribute:: network

        The name of the network this :py:class:`Line` natively belongs to.

    .. attribute:: operator

        The name of the company that operates this line.

    .. py:class:: Line.Request

        Submodel of :py:class:`Searchable.Request`.

    .. py:class:: Line.Results

        Submodel of :py:class:`Searchable.Results`.

    .. note::
        For serialization, the string representation is used for ``linetype``.


LineType
--------

.. py:class:: LineType(name)

    *Submodel of :py:class:`Serializable`.*

    Each :py:class:`Line` has a line type. A line type has one of the values ``(empty string)``, ``train``, ``train.local``, ``train.longdistance``, ``train.longdistance.highspeed``,
    ``urban``, ``metro``, ``tram``, ``bus``, ``bus.regional``, ``bus.city``, ``bus.express``, ``bus.longdistance``, ``suspended``, ``ship``, ``dialable``, or ``other``.

    An empty string means that it can be anyone of the other linetypes, The linetype ``bus`` means that it could be any of the bus-subtypes. The reason for this is that
    not all networks differentiate between some subtyes (e.g. bus types). See the network reference for which linetypes it may output.

    All identical linetypes are the same instance:

    .. code-block:: python

        >>> LineType('bus') is LineType('bus')
        True

    To compare against a linetype, use the ``in`` operator. Be aware that this operator is not transitive!

    .. code-block:: python

        >>> linetype = LineType('bus.express')
        >>> linetype in LineType('bus')
        True
        >>> LineType('bus') in linetype
        False

        >>> LineType('bus') in LineType('')
        True
        >>> LineType('') in LineType('bus')
        False
        >>> LineType('bus') in LineType('bus')
        True

    You can cast a :py:class:`LineType` to string if needed:

    .. code-block:: python

        >>> str(LineType('train.local'))
        'train.local'


LineTypes
---------

.. py:class:: LineTypes(include=('', ), exclude=())

    *Submodel of :py:class:`Serializable`.*

    A selector for :py:class:`LineType` object. It is defined as a list of included line types and a list of excluded linetypes. By default, all line types are included.

    .. code-block:: python

        >>> LineType('bus') in LineTypes()
        True

        >>> LineType('bus') in LineTypes(exclude=('bus', ))
        False
        >>> LineType('bus.express') in LineTypes(exclude=('bus', ))
        False
        >>> LineType('bus') in LineTypes(exclude=('bus.express', ))
        True
        >>> LineType('bus.express') in LineTypes(exclude=('bus.express', ))
        False

        >>> LineType('train') in LineTypes(include=('bus', ), exclude=('bus.express', ))
        False
        >>> LineType('bus') in LineTypes(include=('bus', ), exclude=('bus.express', ))
        True
        >>> LineType('bus.express') in LineTypes(include=('bus', ), exclude=('bus.express', ))
        False

    You can modify the selector using the following methods:

    .. method:: include(*linetypes)

        :param linetypes: one or more line types as string or :py:class:`LineType`

        Make sure that the given line types and all of their subtypes are matched by the selector.

    .. method:: exclude(*linetypes)

        :param linetypes: one or more line types as string or :py:class:`LineType`

        Make sure that the given line types and all of their subtypes are not matched by the selector.

    .. note::
        For serialization, the properties ``included`` and ``excluded`` are created, each one containing a list of string representation of line types.


Trip
----

.. py:class:: Trip

    *Submodel of :py:class:`Searchable`.*

    A connection from a :py:class:`GeoLocation` to another :py:class:`GeoLocation`.

    It consists of a list of :py:class:`TripPart` objects. Just iterate over it to get its elements.

    .. attribute:: time

        The fetching time of this object as a ``datetime`` object. This is relevant to know how up to date the contained real time data (delays, cancellation, platform changes, etc.) is. All APIs set this attribute, but it is not mandatory for input.

    .. attribute:: tickets

        :py:class:`TicketList` of available tickets for this trip.

    .. attention::
        The following attributes are **dynamic** and can not be set.

    .. attribute:: origin

        The start :py:class:`GeoLocation` of this trip.

    .. attribute:: destination

        The end :py:class:`GeoLocation` of this trip.

    .. attribute:: departure

        The departure at the first :py:class:`GeoLocation` of this trip as :py:class:`LiveTime`. (If there are leading :py:class:`Way` objects they need to have the ``duration`` attribute set in order for this to work)

    .. attribute:: arrival

        The arrival at the last :py:class:`GeoLocation` of this trip as :py:class:`LiveTime`. (If there are trailing :py:class:`Way` objects they need to have the ``duration`` attribute set in order for this to work)

    .. attribute:: linetypes

        The line types that occur in this trip as :py:class:`LineTypes`.

    .. attribute:: wayonly

        A boolean indicating whether this Trip only consists of :py:class:`Way` objects.

    .. attribute:: changes

        The number of changes in this trip (number of ``RideSegments`` minus one with a minimum of zero)

    .. attribute:: bike_friendly

        ``False`` if at least one :py:class:`Ride` that is part of this trip is not bike friendly. ``True`` if all of them are. ``None`` if there is no bike friendly information for all rides but those that have the information are bike friendly.

    .. note::
        For serialization, the property ``parts`` is created containing the list of **typed serialized** trip parts.

    .. py:class:: Trip.Request

        Submodel of :py:class:`Searchable.Request`.

        .. attribute:: origin

            **Not None.** The start :py:class:`GeoLocation` of the trip.

        .. attribute:: destination

            **Not None.** The end :py:class:`GeoLocation` of the trip.

        .. attribute:: departure

            The minimum departure time as :py:class:`LiveTime` or ``datetime.datetime``.

            If both times are ``None`` the behaviour is as if you would have set the departure time to the current time right before sending the request. (Default: ``None``)

        .. attribute:: arrival

            The latest allowed arrival as :py:class:`LiveTime` or ``datetime.datetime``. (Default: ``None``)

        .. attribute:: linetypes

            The line types that are allowed as :py:class:`LineTypes`. (Default: all)

        .. attribute:: max_changes

            The maximum number of changes allowed or ``None`` for no limit. (Default: ``None``)

        .. attribute:: with_bike

            Whether a bike should be taken along. (Default: ``False``)

        .. attribute:: wheelchair

            Whether to allow only vehicles that support wheelchairs. (Default: ``False``)

        .. attribute:: low_floor_only

            Whether to allow only low floor vehicles. (Default: ``False``)

        .. attribute:: allow_solid_stairs

            Whether to allow solid stairs. (Default: ``True``)

        .. attribute:: allow_escalators

            Whether to allow escalators. (Default: ``True``)

        .. attribute:: allow_elevators

            Whether to allow elevators. (Default: ``True``)

        .. attribute:: waytype_origin

            Waytype at the beginning of the trip. (Default: walk)

        .. attribute:: waytype_via

            Waytype at changes or ways during the trip. (Default: walk)

        .. attribute:: waytype_destination

            Waytype at the end of the trip. (Default: walk)

        .. attribute:: wayduration_origin

            Maximum duration of a way at the beginning of the trip as a ``datetime.timedelta``. (Default: 10 minutes)

        .. attribute:: wayduration_via

            Maximum duration of changes of ways during the trip as a ``datetime.timedelta``. (Default: 10 minutes)

        .. attribute:: wayduration_destination

            Maximum duration of a way at the end of the trip as a ``datetime.timedelta``. (Default: 10 minutes)

    .. py:class:: Trip.Results

        Submodel of :py:class:`Searchable.Results`.

        .. attribute:: origin

            **Not None.** The start :py:class:`GeoLocation` of the trip.

        .. attribute:: destination

            **Not None.** The end :py:class:`GeoLocation` of the trip.


TripPart
--------

.. py:class:: TripPart

    *Submodel of :py:class:`Serializable`.*

    Abstract base Class for Trip parts


Way
---

.. py:class:: Way(origin: Location, destination: Location, distance: int=None)

    *Submodel of :py:class:`TripPart`.*

    Individual transport (walk, bike, taxi…) with no schedule. Used for example to get from a :py:class:`Address` to a :py:class:`Stop` and for changes but also for trips that are faster by foot.

    .. attribute:: waytype

        **Not None.** The :py:class:`WayType` of this way.

    .. attribute:: origin

        **Not None.** The start point :py:class:`Location`.

    .. attribute:: destination

        **Not None.** The end point :py:class:`Location`.

    .. attribute:: distance

        The distance in meters as ``int``.

    .. attribute:: duration

        The expected duration as ``datetime.timedelta``.

    .. attribute:: path

        The path as a list of :py:class:`Coordinates`.

    .. attribute:: events

        Events on the way (e.g. taking escalators upwards) as a (ordered) list of :py:class:`WayEvent`.

    .. note::
        For serialization, the string representation is used for ``linetype`` and the :py:class:`WayEvent` objects in ``events``.

        The property ``path`` is a list of tuple representations of :py:class:`Coordinates`.


WayType
-------

.. py:class:: WayType(name)

    *Submodel of :py:class:`Serializable`.*

    Each :py:class:`Way` has a line type. A Linetype has one of the values ``walk``, ``bike``, ``car``, ``taxi``.

    All identical way types are the same instance:

    .. code-block:: python

        >>> WayType('walk') is WayType('walk')
        True

    You can cast a :py:class:`WayType` to string if needed:

    .. code-block:: python

        >>> str(WayType('walk'))
        'walk'


WayEvent
--------

.. py:class:: WayEvent(name, direction)

    *Submodel of :py:class:`Serializable`.*

    A way :py:class:`Way` events one of the names ``stairs``, ``escalator`` or ``elevator`` and one of the directions ``up`` or ``down``.

    All identical way types are the same instance:

    .. code-block:: python

        >>> WayType('escalator', 'down') is WayType('escalator', 'down')
        True

    You can cast a :py:class:`WayEvent` to string or tuple if needed:

    .. code-block:: python

        >>> str(WayEvent('escalator, 'down'))
        'escalator.down'
        >>> tuple(WayEvent('escalator, 'down'))
        ('escalator', 'down')

    .. attention::
        The following attributes are **dynamic** and can not be set.

    .. attribute:: name

        **Not None.** ``stairs``, ``escalator`` or ``elevator``

    .. attribute:: direction

        **Not None.** ``up`` or ``down``


TicketList
----------

.. py:class:: TicketList(all_types: bool=True)

    *Submodel of :py:class:`Serializable`.*

    A list of tickets.

    .. attribute:: currency

        **Not None.** The name or abbreviation of the currency.

    .. attribute:: level_name

        How a level is named at this network.

    .. attribute:: single

        **Not None.** The single ticket as :py:class:`TicketData`.

    .. attribute:: bike

        The single ticket as :py:class:`TicketData`.

    .. attribute:: other

        **Not None.** Other available tickets as a dictionary with the name of the tickets as keys and :py:class:`TicketData` objects as values.


TicketData
----------

Submodels of :py:class:`Serializable`.

.. py:class:: TicketData(authority=None, level=None, price=None, price_child=None)

    *Submodel of :py:class:`Serializable`.*

    Information about a ticket.

    .. attribute:: authority

        The name of the authority selling this ticket.

    .. attribute:: level

        The level of this ticket, e.g. A or something similar, depending on the network

    .. attribute:: price

        **Not None.** The price of this ticket as float.

    .. attribute:: price_child

        The children’s price for this ticket if this ticket is not a ticket for children only but has a different price for children.
