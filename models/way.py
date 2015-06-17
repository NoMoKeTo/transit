#!/usr/bin/env python3
from .base import Serializable, TripPart
from .locations import AbstractLocation, Coordinates
from datetime import timedelta


class Way(TripPart):
    def __init__(self, waytype=None, origin=None, destination=None, distance=None):
        super().__init__()
        self.waytype = WayType('walk') if waytype is None else waytype
        self.origin = origin
        self.destination = destination
        self.distance = None
        self.duration = None
        self.events = None
        self.path = None

    @classmethod
    def _validate(cls):
        return (
            ('waytype', WayType),
            ('origin', AbstractLocation),
            ('destination', AbstractLocation),
            ('distance', (None, int, float)),
            ('duration', timedelta),
            ('events', None),
            ('path', None),
        )

    def _validate_custom(self, name, value):
        if name == 'path':
            if value is None:
                return True
            for v in value:
                if not isinstance(v, Coordinates):
                    return False
            return True
        elif name == 'events':
            if value is None:
                return True
            for v in value:
                if not isinstance(v, WayEvent):
                    return False
            return True

    def _serialize_custom(self, name):
        if name == 'path':
            return 'path', [p.serialize() for p in self.path] if self.path is not None else None
        elif name == 'events':
            return 'events', [e.serialize() for e in self.events] if self.events is not None else None

    def _unserialize_custom(self, name, data):
        if name == 'path':
            self.path = [Coordinates.unserialize(p) for p in data]
        if name == 'events':
            self.events = [WayEvent.unserialize(e) for e in data]

    def __eq__(self, other):
        return (isinstance(other, Way) and self.waytype == other.waytype and
                self.origin == other.origin and self.destination == other.destination)

    def __repr__(self):
        distance = ''
        if self.distance:
            distance = ' %dm' % self.distance
        return '<Way %s %dmin%s %s %s>' % (str(self.waytype), self.duration.total_seconds() / 60, distance, repr(self.origin), repr(self.destination))


class WayType(Serializable):
    _known = ('walk', 'bike', 'car', 'taxi')
    _created = {}

    def __new__(cls, value=''):
        if isinstance(value, cls):
            return value
        elif value not in cls._known and not value.startswith("unknown:"):
            raise AttributeError('invalid waytype: %s' % repr(value))
        if value in cls._created:
            return cls._created[value]
        else:
            self = super().__new__(cls)
            self._value = value
            cls._created[value] = self
            return self

    def _serialize(self):
        return self._value

    @classmethod
    def unserialize(cls, data):
        return cls(data)

    def __repr__(self):
        return 'WayType(%s)' % repr(self._value)

    def __str__(self):
        return self._value

    def __eq__(self, other):
        return other._value == self._value


class WayEvent(Serializable):
    _created = {}

    def __new__(cls, name='', direction=''):
        if isinstance(name, cls):
            return name
        assert name in ('stairs', 'elevator', 'escalator')
        assert direction in ('up', 'down')
        value = (name, direction)
        if value in cls._created:
            return cls._created[value]
        else:
            self = super().__new__(cls)
            self._value = value
            cls._created[value] = self
            return self

    def _serialize(self):
        return self._value

    @classmethod
    def unserialize(cls, data):
        return cls(*data)

    def __repr__(self):
        return 'WayEvent%s' % repr(self._value)

    def __iter__(self):
        return self._value

    def __eq__(self, other):
        return isinstance(other, WayEvent) and self._value == other._value

    @property
    def name(self):
        return self._value[0]

    @property
    def direction(self):
        return self._value[1]
