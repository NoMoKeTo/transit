#!/usr/bin/env python3
from .base import Collectable, Serializable
from . import fields


class Line(Collectable):
    linetype = fields.Model('LineType')
    product = fields.Field(str)
    name = fields.Field(str, none=False)
    shortname = fields.Field(str, none=False)
    route = fields.Field(str)
    first_stop = fields.Model('Stop')
    last_stop = fields.Model('Stop')
    network = fields.Field(str)
    operator = fields.Field(str)

    def __init__(self, linetype=None, **kwargs):
        super().__init__(linetype=(LineType() if linetype is None else linetype), **kwargs)

    def __eq__(self, other):
        if not isinstance(other, Line):
            return False

        if self.linetype not in other.linetype and other.linetype not in self.linetype:
            return False

        by_id = self._same_by_id(other)
        if by_id is not None:
            return by_id

        first = None
        if self.first_stop is not None and other.first_stop is not None:
            first = self.first_stop == other.first_stop
        if first is False:
            return False

        last = None
        if self.last_stop is not None and other.last_stop is not None:
            last = self.last_stop == other.last_stop
        if last is False:
            return False

        if self.route != other.route:
            return False

        return None

    def __repr__(self):
        return '<Line %s %s>' % (str(self.linetype), repr(self.name))


class LineType(Serializable):
    _known = (
        '', 'train', 'train.local', 'train.longdistance', 'train.longdistance.highspeed',
        'urban', 'metro', 'tram',
        'bus', 'bus.regional', 'bus.city', 'bus.express', 'bus.longdistance',
        'suspended', 'ship', 'dialable', 'other'
    )
    _created = {}

    def __new__(cls, value=''):
        if isinstance(value, cls):
            return value
        elif value not in cls._known:
            raise AttributeError('invalid linetype: %s' % repr(value))
        if value in cls._created:
            return cls._created[value]
        else:
            self = super().__new__(cls)
            self._value = value
            cls._created[value] = self
            return self

    def serialize(self, **kwargs):
        return self._value

    @classmethod
    def unserialize(cls, data):
        return cls(data)

    def __repr__(self):
        return 'LineType(%s)' % repr(self._value)

    def __str__(self):
        return self._value

    def __contains__(self, other):
        if type(other) == str:
            other = LineType(other)
        return other._value.startswith(self._value)


class LineTypes(Serializable):
    _included = fields.Set(fields.Model(LineType))
    _excluded = fields.Set(fields.Model(LineType))

    def __init__(self, include=('', ), exclude=()):
        super().__init__()
        self._included = set([LineType(s) for s in include])
        self._excluded = set([LineType(s) for s in exclude])

    def _unserialize(self, data):
        if 'include' in data:
            self._included = set([LineType(s) for s in data['include']])
        if 'exclude' in data:
            self._excluded = set([LineType(s) for s in data['exclude']])

    def __repr__(self):
        args = []
        if tuple(self._included) != ('', ):
            args.append('%s' % repr(tuple(str(s) for s in self._included)))
        if self._excluded:
            args.append(('exclude=' if not args else '') + '%s' % repr(tuple(str(s) for s in self._excluded)))
        return 'LineTypes(%s)' % ', '.join(args)

    def include(self, *args):
        args = [LineType(a) for a in args]
        for include in args[:]:
            args = [a for a in args if a not in include or a is include]
        args = list(set(args))

        if not args:
            return

        for include in args:
            self._included = [i for i in self._included if i not in include]
            self._exclude = [e for e in self._excluded if e in include]

        self._included = set(self._included + args)
        self._excluded = set([e for e in self._excluded if [i for i in self._included if e in i]])

    def exclude(self, *args):
        args = [LineType(a) for a in args]
        for exclude in args[:]:
            args = [a for a in args if a not in exclude or a is exclude]
        args = list(set(args))

        if not args:
            return

        for exclude in args:
            self._included = [i for i in self._included if i not in exclude]
            self._exclude = [e for e in self._excluded if e in exclude]

        self._included = set(self._included)
        self._excluded = set(self._excluded + args)
        self._excluded = set([e for e in self._excluded if [i for i in self._included if e in i]])

    def __contains__(self, linetype):
        linetype = LineType(linetype)
        for exclude in self._excluded:
            if linetype in exclude:
                return False

        for include in self._included:
            if linetype in include:
                return True

        return False
