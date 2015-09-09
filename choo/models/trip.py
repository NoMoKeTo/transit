#!/usr/bin/env python3
from .base import Searchable, TripPart
from .way import WayType
from .locations import Location, GeoLocation
from .ride import Ride, RideSegment
from .line import Line, LineType, LineTypes
from .tickets import TicketList
from datetime import timedelta, datetime
from . import fields


class Trip(Searchable):
    _parts = fields.List(fields.Model(TripPart, none=False))
    tickets = fields.Model(TicketList)

    def __init__(self, **kwargs):
        # magic, do not remove
        super().__init__(**kwargs)

    class Request(Searchable.Request):
        walk_speed = fields.Field(str, default='normal')
        origin = fields.Model(GeoLocation)
        via = fields.List(fields.Model(GeoLocation))
        destination = fields.Model(GeoLocation)
        departure = fields.Model(datetime)
        arrival = fields.Model(datetime)
        linetypes = fields.Model(LineTypes)
        max_changes = fields.Field(int)

        with_bike = fields.Field(bool, default=False)
        wheelchair = fields.Field(bool, default=False)
        low_floor_only = fields.Field(bool, default=False)
        allow_solid_stairs = fields.Field(bool, default=True)
        allow_escalators = fields.Field(bool, default=True)
        allow_elevators = fields.Field(bool, default=True)

        waytype_origin = fields.Model(WayType, default=WayType('walk'))
        waytype_via = fields.Model(WayType, default=WayType('walk'))
        waytype_destination = fields.Model(WayType, default=WayType('walk'))

        wayduration_origin = fields.Field(timedelta, default=timedelta(minutes=10))
        wayduration_via = fields.Field(timedelta, default=timedelta(minutes=10))
        wayduration_destination = fields.Field(timedelta, default=timedelta(minutes=10))

        def __init__(self, **kwargs):
            # magic, do not remove
            super().__init__(**kwargs)

        def _matches(self, obj):
            if self.origin != obj.origin or self.destination != obj.destination:
                return False

            if not obj.wayonly:
                if self.departure is not None and self.departure < obj.departure:
                    return False

                if self.arrival is not None and self.arrival > obj.arrival:
                    return False

            for i, part in enumerate(obj):
                if isinstance(part, RideSegment):
                    if part.line.linetype not in self.linetypes:
                        return False
                else:
                    if part.waytype == WayType('walk'):
                        continue
                    if i == 0:
                        if self.waytype_origin != part.waytype:
                            return False
                    elif i + 1 == len(obj):
                        if self.waytype_destination != part.waytype:
                            return False
                    else:
                        if self.waytype_via != part.waytype:
                            return False

            return True

    class Results(Searchable.Results):
        origin = fields.Model(Location, none=True)
        via = fields.Model(Location, none=True)
        destination = fields.Model(Location, none=True)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    @property
    def origin(self):
        return self._parts[0].origin

    @property
    def destination(self):
        return self._parts[-1].destination

    @property
    def departure(self):
        delta = timedelta(0)
        for part in self._parts:
            if isinstance(part, RideSegment):
                return (part.departure - delta) if part.departure else None
            elif part.duration is None:
                return None
            else:
                delta += part.duration

    @property
    def arrival(self):
        delta = timedelta(0)
        for part in reversed(self._parts):
            if isinstance(part, RideSegment):
                return (part.arrival + delta) if part.arrival else None
            elif part.duration is None:
                return None
            else:
                delta += part.duration

    @property
    def wayonly(self):
        for part in self:
            if isinstance(part, RideSegment):
                return False
        return True

    @property
    def linetypes(self):
        types = LineTypes(())
        for part in self._parts:
            if isinstance(part, RideSegment):
                types.include(part.line.linetype)
        return types

    @property
    def changes(self):
        changes = -1
        for part in self._parts:
            if isinstance(part, RideSegment):
                changes += 1
        return max(0, changes)

    @property
    def bike_friendly(self):
        for part in self._parts:
            if not isinstance(part, RideSegment):
                continue
            if part.bike_friendly is None:
                return None
            elif part.bike_friendly is False:
                return False
        return True

    def to_request(self):
        r = Trip.Request()
        r.walk_speed = self.walk_speed
        r.origin = self.origin
        r.destination = self.destination
        r.departure = self.departure
        r.arrival = self.arrival
        r.linetypes = self.linetypes
        r.max_changtes = self.max_changes
        r.bike_friendly = self.bike_friendly
        return r

    def __len__(self):
        return len(self._parts)

    def __getitem__(self, key):
        return self._parts[key]

    def __contains__(self, obj):
        if isinstance(obj, RideSegment):
            return obj in self._parts

        if isinstance(obj, Ride):
            compare = lambda part, obj: part.ride == obj
        elif isinstance(obj, Ride.Request):
            compare = lambda part, obj: part.ride.matches(obj)
        elif isinstance(obj, Line):
            compare = lambda part, obj: part.line == obj
        elif isinstance(obj, Line.Request):
            compare = lambda part, obj: part.line.matches(obj)
        elif isinstance(obj, LineType):
            compare = lambda part, obj: part.line.linetype == obj
        elif isinstance(obj, LineTypes):
            compare = lambda part, obj: part.line.linetype in obj
        else:
            # todo: here be more, Way, Stop, Platform, …
            raise NotImplementedError()

        for part in self.parts:
            if isinstance(part, RideSegment) and compare(part, obj):
                return True
        return False

    def __repr__(self):
        return '<Trip %s %s - %s %s>' % (repr(self.origin), str(self.departure), repr(self.origin), str(self.arrival))

    def __eq__(self, other):
        if not isinstance(other, Trip):
            return False

        for i, part in enumerate(self):
            compared = part == other[i]
            if compared is not True:
                return compared
        return True

    def __iter__(self):
        yield from self._parts
