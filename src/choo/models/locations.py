#!/usr/bin/env python3
from .base import Serializable, Searchable, Collectable
from . import fields


class GeoLocation(Serializable):
    lat = fields.Field(float)
    lon = fields.Field(float)

    def __init__(self, **kwargs):
        if self.__class__ == GeoLocation:
            raise RuntimeError('Only instances of GeoLocation subclasses are allowed!')
        super().__init__(**kwargs)

    def to_coordinates(self, **kwargs):
        if self.lat is None or self.lon is None:
            return None
        return Coordinates(self.lat, self.lon)

    def __eq__(self, other):
        return (isinstance(other, GeoLocation) and
                self.lat is not None and other.lat == self.lat and
                self.lon is not None and other.lon == self.lon)

    def __repr__(self):
        return 'GeoLocation(%.6f, %.6f)' % (self.lat, self.lon)

    def _near(self, other):
        return (self.lat is not None and other.lat is not None and
                self.lon is not None and other.lon is not None and
                abs(self.lat - other.lat) < 0.02 and
                abs(self.lon - other.lon) < 0.02)

    def _not_too_far(self, other):
        return ((self.lat is not None and other.lat is not None and
                 self.lon is not None and other.lon is not None) and
                (abs(self.lat - other.lat) < 0.04 or
                 abs(self.lon - other.lon) < 0.04))


class Coordinates(GeoLocation):
    def __init__(self, lat=None, lon=None, **kwargs):
        if lat is None or lon is None:
            raise ValueError('latitude and longitude has to be not None')
        super().__init__(lat=lat, lon=lon, **kwargs)

    def __iter__(self):
        return iter([self.lat, self.lon])

    @classmethod
    def unserialize(cls, data):
        if isinstance(data, (list, tuple)):
            return cls(*data)
        else:
            return super(GeoLocation, cls).unserialize(data)


class Platform(Collectable, GeoLocation):
    stop = fields.Model('Stop', none=False)
    ifopt = fields.Field(str)
    name = fields.Field(str)
    full_name = fields.Field(str)

    def __init__(self, stop=None, name=None, full_name=None, **kwargs):
        super().__init__(stop=stop, name=name, full_name=full_name, **kwargs)

    def __repr__(self):
        return 'Platform(%s, %s, %s)' % (repr(self.stop), repr(self.name), repr(self.full_name))

    def __eq__(self, other):
        if not isinstance(other, Platform):
            return False

        by_id = self._same_by_id(other)
        if by_id is not None:
            return by_id

        if self.ifopt is not None and self.ifopt == other.ifopt:
            return True

        if self.stop != other.stop:
            return False

        if self.coords is not None and self.coords == other.coords:
            return True

        return None


class Location(Collectable, GeoLocation):
    country = fields.Field(str)
    city = fields.Field(str)
    name = fields.Field(str)
    near_stops = fields.Model('Stop.Results')

    def __init__(self, country=None, city=None, name=None, **kwargs):
        if self.__class__ == Location:
            raise RuntimeError('Only instances of Location subclasses are allowed!')
        super().__init__(country=country, city=city, name=name, **kwargs)

    def __repr__(self):
        return '%s(%s, %s, %s)' % (self.__class__.__name__, repr(self.country), repr(self.city), repr(self.name))

    def __eq__(self, other):
        if not isinstance(other, Location):
            return False

        by_id = self._same_by_id(other)
        if by_id is not None:
            return by_id

        if (self.city is not None and self.city == other.city) or self._not_too_far(other):
            if self.name is not None and self.name == other.name:
                return True

        return None

    class Request(Searchable.Request):
        name = fields.Field(str)
        city = fields.Field(str)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.name = None
            self.city = None

    class Result(Searchable.Result):
        score = fields.Field(int)
        distance = fields.Field(int)
        duration = fields.Timedelta()


class Stop(Location):
    full_name = fields.Field(str)
    ifopt = fields.Field(str)
    uic = fields.Field(str)
    rides = fields.Model('Ride.Results')
    lines = fields.Model('Line.Results')

    def __init__(self, country=None, city=None, name=None, **kwargs):
        super().__init__(country=country, city=city, name=name, **kwargs)

    def serialize(self, **kwargs):
        if 'stops_had_results' not in kwargs:
            kwargs['stops_had_results'] = []

        if self.id not in kwargs['stops_had_results']:
            kwargs['stops_had_results'].append(self.id)
        else:
            kwargs['exclude'] = ['rides', 'lines']

        return super().serialize(**kwargs)

    def __repr__(self):
        return '<Stop %s>' % repr(self.full_name if self.full_name else (self.city, self.name))

    def __eq__(self, other):
        if not isinstance(other, Stop):
            return False

        by_id = self._same_by_id(other)
        if by_id is True:
            return True

        if (self.full_name is not None and other.full_name is not None and
                self.full_name.replace(',', '') == other.full_name.replace(',', '')):
            return True

        if self.city is not None and other.city is not None:
            if self.city.split(' ')[0].lower() != other.city.split(' ')[0].lower():
                return False

            if self.city.startswith(other.city) and other.city.startswith(self.city):
                return self.name == other.name

        return None


class POI(Location):
    def __init__(self, country=None, city=None, name=None, **kwargs):
        super().__init__(country=country, city=city, name=name, **kwargs)

    @property
    def full_name(self):
        if self.city is None:
            return self.name
        else:
            return '%s, %s' % (self.city, self.name)

    def __eq__(self, other):
        if not isinstance(other, POI):
            return False

        return super().__eq__(other)


class Address(Location):
    street = fields.Field(str)
    number = fields.Field(str)

    def __init__(self, country=None, city=None, name=None, **kwargs):
        super().__init__(country=country, city=city, name=name, **kwargs)

    @property
    def full_name(self):
        if self.city is None:
            return self.name
        else:
            return '%s, %s' % (self.city, self.name)

    def __eq__(self, other):
        if not isinstance(other, Address):
            return False

        return super().__eq__(other)
