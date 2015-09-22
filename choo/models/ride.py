#!/usr/bin/env python3
from .base import Serializable, Collectable, TripPart
from .locations import Coordinates
from .ridepoint import RidePoint
from .line import Line
from . import fields


class RideIterable(Serializable):
    def __init__(self, **kwargs):
        if self.__class__ == RideIterable:
            raise RuntimeError('Only instances of RideIterable subclasses are allowed!')
        super().__init__(**kwargs)

    @property
    def is_complete(self):
        return None not in self

    def __len__(self):
        i = 0
        for elem in self._elems():
            i += 1
        return i

    def _get_elem(self, key, silent=False):
        if key is None:
            return None
        if key < 0:
            elem = self._last
            for i in range(1+key):
                if elem is self._first:
                    raise IndexError('%s index out of range' % self.__class__.__name__)
                elem = elem.prev
            return elem

        elem = self._first
        for i in range(key):
            if elem is self._last:
                raise IndexError('%s index out of range' % self.__class__.__name__)
            elem = elem.next
        return elem

    def __getitem__(self, key):
        if not isinstance(key, (int, slice)):
            raise TypeError('%s indices must be integers, not %s' % (self.__class__.__name__, type(key).__name__))

        if isinstance(key, slice):
            if key.step is not None:
                raise TypeError('%s cannot be sliced with steps', self.__class__.__name__)
            if not ((key.start is None or isinstance(key.start, int)) and
                    (key.stop is None or isinstance(key.stop, int))):
                raise TypeError('slice indices must be integers or None')

            return RideSegment(self, self._get_elem(key.start), self._get_elem(key.stop))

        return self._get_elem(key).point

    def __iter__(self):
        for elem in self._elems():
            yield elem.point

    def _elems(self):
        elem = self._first
        while True:
            yield elem
            if elem == self._last:
                break
            elem = elem.next

    def index(self, item):
        if item is not None and not isinstance(item, RidePoint):
            raise TypeError('%s elements must be RidePoints, not %s' % (self.__class__.__name__, type(item).__name__))

        for i, point in enumerate(self):
            if point == item:
                return i
        raise ValueError('%s is not in %s' % (repr(item), self.__class__.__name__))

    def _elem_index(self, item):
        assert isinstance(item, RideIterable.Element)

        for i, elem in enumerate(self._elems()):
            if elem is item:
                return i
        raise ValueError('%s is not in %s' % (repr(item), self.__class__.__name__))

    def __contains__(self, item):
        try:
            self.index(item)
        except(ValueError):
            return False
        return True

    @property
    def path(self):
        # todo
        raise NotImplementedError

    class Element:
        def __init__(self, point, prev=None, next=None):
            self.point = point
            self.prev = prev
            self.next = next
            self.path_to_next = None


class Ride(Collectable, RideIterable):
    time = fields.DateTime()
    line = fields.Model(Line, none=False)
    number = fields.Field(str)
    direction = fields.Field(str)
    canceled = fields.Field(bool)
    bike_friendly = fields.Field(bool)
    infotexts = fields.List(str)

    def __init__(self, line=None, number=None, **kwargs):
        self._first = self._last = None
        super().__init__(line=line, number=number, **kwargs)

    def validate(self):
        for point in self:
            if point is None:
                continue
            point.validate()

        return super().validate()

    def serialize(self, **kwargs):
        data = super().serialize(**kwargs)
        data['stops'] = [(p.serialize(**kwargs) if p is not None else None) for p in self]
        # todo
        # data['paths'] = {int(i): [tuple(p) for p in path] for i, path in self._paths.items()}
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

        for elem in self._elems():
            if elem.point is None:
                continue
            newpoint = elem.point.apply_recursive(**kwargs)
            if newpoint is not None:
                elem.point = newpoint

        return super().apply_recursive(**kwargs)

    def __setitem__(self, key, item):
        if not isinstance(key, int):
            raise TypeError('Ride indices must be integers, not %s' % type(key).__name__)
        if item is not None and not isinstance(item, RidePoint):
            raise TypeError('Ride elements must be RidePoints or None, not %s' % type(item).__name__)

        self._get_elem(key).point = item

    def __delitem__(self, key):
        self.pop(key)

    def append(self, item):
        if item is not None and not isinstance(item, RidePoint):
            raise TypeError('Ride elements must be RidePoints or None, not %s' % type(item).__name__)

        elem = RideIterable.Element(item, prev=self._last)

        if self._first is None:
            self._first = self._last = elem
            return

        if self[-1] is item is None:
            return

        self._last.next = elem
        self._last = elem

    def prepend(self, item):
        if item is not None and not isinstance(item, RidePoint):
            raise TypeError('Ride elements must be RidePoints or None, not %s' % type(item).__name__)

        elem = RideIterable.Element(item, next=self._first)

        if self._first is None:
            self._first = self._last = elem
            return

        if self[0] is item is None:
            return

        self._first.prev = elem
        self._first = elem

    def insert(self, position, item):
        if not isinstance(position, int):
            raise TypeError('Ride indices must be integers, not %s' % type(position).__name__)
        if item is not None and not isinstance(item, RidePoint):
            raise TypeError('Ride elements must be RidePoints or None, not %s' % type(item).__name__)

        try:
            elem = self._get_elem(position)
        except(IndexError):
            if position == len(self):
                return self.append(item)
            else:
                raise

        if elem == self._first:
            return self.prepend(item)

        newelem = RideIterable.Element(item, prev=elem.prev, next=elem)
        elem.prev.next = newelem
        elem.prev = newelem

    def _remove_elem(self, elem):
        if elem != self._first:
            elem.prev.next = elem.next
        else:
            self._first = elem.next
        if elem != self._last:
            elem.next.prev = elem.prev
        else:
            self._last = elem.prev

        if elem.prev is not None and elem.next is not None and elem.prev.pointer is elem.next.pointer is None:
            self._remove_elem(elem.next)

        elem.next = elem.prev = None

    def remove(self, item):
        if item is None:
            raise TypeError('Ride.remove(x): can not remove all Nones')

        if not isinstance(item, RidePoint):
            raise TypeError('Ride elements must be RidePoints or None, not %s' % type(item).__name__)

        for elem in self._elems():
            if elem.point == item:
                self._remove_elem(elem)
                return

        raise ValueError('Ride.remove(x): x not in Ride')

    def pop(self, key=-1):
        if not isinstance(key, int):
            raise TypeError('Ride indices must be integers, not %s' % type(key).__name__)

        elem = self._get_elem(key)
        self._remove_elem(elem)
        return elem.point

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

        for point in self:
            if point is None:
                continue
            for point2 in self:
                if point2 is None:
                    continue
                if point == point2:
                    return True

        return None

    def __repr__(self):
        return '<Ride %s %s>' % (self.number, repr(self.line))

    class Results(Collectable.Results):
        results = fields.List(fields.Tuple(fields.Model('RideSegment'), fields.Field(int)))

        def __init__(self, results=[], scored=False):
            self.content = RideSegment
            super().__init__(results, scored)


class RideSegment(TripPart, RideIterable):
    ride = fields.Model(Ride, none=False)

    def __init__(self, ride=None, origin=None, destination=None, **kwargs):
        super().__init__(**kwargs)
        print(origin, destination)
        self.ride = ride
        self._origin = origin
        self._destination = destination

    @property
    def _first(self):
        return self.ride._first if self._origin is None else self._origin

    @property
    def _last(self):
        return self.ride._last if self._destination is None else self._destination

    def validate(self):
        assert self._origin is None or isinstance(self._origin, RideIterable.Element)
        assert self._destination is None or isinstance(self._destination, RideIterable.Element)
        return super().validate()

    def serialize(self, **kwargs):
        data = super().serialize(**kwargs)
        if self._origin is not None:
            data['origin'] = self.ride._elem_index(self._origin)

        if self._destination is not None:
            data['destination'] = self.ride._elem_index(self._destination)
        return data

    @classmethod
    def unserialize(cls, data):
        self = super(RideSegment, cls).unserialize(data)

        origin = data.get('origin')
        if origin is not None:
            self._origin = self.ride._get_elem(origin)

        destination = data.get('destination')
        if destination is not None:
            self._destination = self.ride._get_elem(destination)

        return self

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
