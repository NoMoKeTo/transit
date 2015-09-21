#!/usr/bin/env python3
from .base import Collectable, TripPart
from .locations import Coordinates
from .ridepoint import RidePoint
from .line import Line
from . import fields


class Ride(Collectable):
    time = fields.DateTime()
    line = fields.Model(Line, none=False)
    number = fields.Field(str)
    direction = fields.Field(str)
    canceled = fields.Field(bool)
    bike_friendly = fields.Field(bool)
    infotexts = fields.List(str)

    def __init__(self, line=None, number=None, **kwargs):
        self._stops = kwargs.get('_stops', [])
        self._paths = kwargs.get('_paths', {})
        super().__init__(line=line, number=number, **kwargs)

    def validate(self):
        # _stops
        assert isinstance(self._stops, list)
        for k, v in self._stops:
            assert isinstance(k, Ride.StopPointer)
            assert v is None or isinstance(v, RidePoint)

        # _paths
        assert isinstance(self._paths, dict)
        for k, v in self._paths.items():
            assert isinstance(k, Ride.StopPointer)
            assert isinstance(v, list)
            for item in v:
                assert isinstance(item, Coordinates)

        return super().validate()

    def serialize(self, **kwargs):
        data = super().serialize(**kwargs)
        data['stops'] = [(s.serialize(**kwargs) if s else None) for i, s in self._stops]
        data['paths'] = {int(i): [tuple(p) for p in path] for i, path in self._paths.items()}
        return data

    @classmethod
    def unserialize(cls, data):
        self = super(Ride, cls).unserialize(data)

        for s in data.get('stops', []):
            self.append(RidePoint.unserialize(s) if s is not None else None)

        for i, path in data.get('paths', {}).items():
            self._paths[self.pointer(int(i))] = [Coordinates.unserialize(p) for p in path]

        return self

    def apply_recursive(self, **kwargs):
        if 'time' in kwargs:
            self.time = kwargs['time']

        for i, kv in enumerate(self._stops):
            k, v = kv
            if v is not None:
                newv = v.apply_recursive(**kwargs)
                if newv is not None:
                    self._stops[i] = (k, newv)

        return super().apply_recursive(**kwargs)

    @property
    def is_complete(self):
        return None not in self._stops

    def pointer(self, i):
        return self._stops[int(i)][0]

    def __len__(self):
        return len(self._stops)

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.step is not None:
                raise TypeError('Ride cannot be sliced with steps')
            return RideSegment(self,
                               self.pointer(key.start) if key.start else None,
                               self.pointer(key.stop) if key.stop else None)
        else:
            return self._stops[int(key)][1]

    def __setitem__(self, key, item):
        assert isinstance(item, RidePoint) or item is None
        self._stops[int(key)][1] = item

    def __delitem__(self, key):
        key = int(key)
        del self._stops[key]
        self._alter_pointers_after(key - 1, -1)

    def __iter__(self, key):
        for stop in self._stops:
            yield stop[1]

    def items(self, key):
        for stop in self._stops:
            yield stop

    def _alter_pointers_after(self, pos: int, diff: int):
        for stop in self._stops[pos + 1:]:
            stop[0]._i += diff

    def append(self, item):
        assert isinstance(item, RidePoint) or item is None
        pointer = Ride.StopPointer(len(self._stops))
        self._stops.append((pointer, item))
        return pointer

    def prepend(self, item):
        assert isinstance(item, RidePoint) or item is None
        pointer = Ride.StopPointer(0)
        self._stops.insert(0, (pointer, item))
        self._alter_pointers_after(0, 1)
        return pointer

    def insert(self, position, item):
        assert isinstance(item, RidePoint) or item is None
        position = max(0, min(position, len(self._stops)))
        pointer = Ride.StopPointer(position)
        self._stops.insert(position, (pointer, item))
        self._alter_pointers_after(position, 1)
        return pointer

    def __eq__(self, other):
        if not isinstance(other, Ride):
            return False

        by_id = self._same_by_id(other)
        if by_id is not None:
            return by_id

        if self.line is not None and other.line is not None and self.line != other.line:
            return False

        if self.number is not None and other.number is not None and self.number != other.number:
            return False

        if self[-1] is not None and other[-1] is not None and self[-1].stop != other[-1].stop:
            return False

        if self[0] is not None and other[0] is not None and self[0].stop != other[0].stop:
            return False

        for stop in self._stops[1:-1]:
            if stop[1] is None:
                continue
            for stop2 in other._stops[1:-1]:
                if stop2[1] is None:
                    continue
                if stop[1] == stop2[1]:
                    return True

        return None

    @property
    def path(self, origin=None, destination=None):
        # todo
        raise NotImplementedError

    def __repr__(self):
        return '<Ride %s %s>' % (self.number, repr(self.line))

    class StopPointer():
        def __init__(self, i: int):
            self._i = i

        def __int__(self):
            return self._i

        def __index__(self):
            return self._i

        def __repr__(self):
            return 'p:%d' % self._i

    class Results(Collectable.Results):
        results = fields.List(fields.Tuple(fields.Model('RideSegment'), fields.Field(int)))

        def __init__(self, results=[], scored=False):
            self.content = RideSegment
            super().__init__(results, scored)


class RideSegment(TripPart):
    ride = fields.Model(Ride, none=False)

    def __init__(self, ride=None, _origin=None, _destination=None, **kwargs):
        self._origin = _origin
        self._destination = _destination
        super().__init__(ride=ride, **kwargs)

    def validate(self):
        assert self._origin is None or isinstance(self._origin, Ride.StopPointer)
        assert self._destination is None or isinstance(self._destination, Ride.StopPointer)
        return super().validate()

    def serialize(self, **kwargs):
        data = super().serialize(**kwargs)
        if self._origin is not None:
            data['origin'] = int(self._origin)

        if self._destination is not None:
            data['destination'] = int(self._destination)
        return data

    @classmethod
    def unserialize(cls, data):
        self = super(RideSegment, cls).unserialize(data)

        if 'origin' in data:
            self._origin = self.ride.pointer(data['origin'])

        if 'destination' in data:
            self._destination = self.ride.pointer(data['destination'])

        return self

    def _stops(self):
        if self._destination is None:
            return self.ride._stops[self._origin:None]
        else:
            return self.ride._stops[self._origin:int(self._destination) + 1]

    @property
    def path(self, origin=None, destination=None):
        # todo
        raise NotImplementedError

    @property
    def is_complete(self):
        return None not in self._stops()

    def __len__(self):
        return len(self._stops)

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.step is not None:
                raise TypeError('RideSegment cannot be slices with steps')
            if self._origin is not None:
                if type(key.start) != int:
                    start = key.start
                elif key.start >= 0:
                    start = int(self._origin) + key.start
                else:
                    start = int(self._destination) + 1 - key.start
                if type(key.stop) != int:
                    stop = key.stop
                elif key.start >= 0:
                    stop = int(self._origin) + key.stop
                else:
                    stop = int(self._destination) + 1 - key.stop
            else:
                start, stop = key.start, key.stop
            return RideSegment(self.ride, start, stop)
        else:
            if type(key) != int:
                return self.ride[key]
            else:
                return self._stops()[key][1]

    def __iter__(self, key=None):
        for stop in self._stops():
            yield stop[1]

    def items(self):
        for stop in self._stops():
            yield stop

    @property
    def origin(self):
        return self[0].stop

    @property
    def destination(self):
        return self[-1].stop

    @property
    def departure(self):
        return self[0].departure

    @property
    def arrival(self):
        return self[-1].arrival

    def __getattr__(self, name):
        return getattr(self.ride, name)

    def __eq__(self, other):
        if not isinstance(other, RideSegment):
            return False

        if self.ride is other.ride:
            return self._origin == other._origin and self._destination == other._destination
        elif self.ride == other.ride:
            return (self.origin == other.origin and self.departure == other.departure and
                    self.destination == other.destination and self.arrival == other.arrival)
        return False

    def __repr__(self):
        return '<RideSegment %s %s %s>' % (repr(self.origin), repr(self.destination), repr(self.ride))
