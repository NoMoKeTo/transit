from typing import Union

from ..types import Coordinates
from .base import Field, Model


class Location(Model):
    coords = Field(Coordinates)


class Platform(Location):
    stop = Field(Union['Stop'])
    ifopt = Field(str)
    name = Field(str)
    full_name = Field(str)

    def __init__(self, stop=None, name=None, full_name=None, **kwargs):
        super().__init__(stop=stop, name=name, full_name=full_name, **kwargs)

    def __repr__(self):
        return 'Platform(%s, %s, %s)' % (repr(self.stop), repr(self.name), repr(self.full_name))

    def __eq__(self, other):
        if not isinstance(other, Platform):
            return False

        if self.stop != other.stop:
            return False

        if self.coords is not None and self.coords == other.coords:
            return True

        return None


class Address(Location):
    country = Field(str)
    city = Field(str)
    address = Field(str)
    street = Field(str)
    number = Field(str)
    # near_stops = fields.Model('Stop.Results')

    def __init__(self, country=None, city=None, name=None, **kwargs):
        if self.__class__ == Location:
            raise RuntimeError('Only instances of Location subclasses are allowed!')
        super().__init__(country=country, city=city, name=name, **kwargs)

    def __repr__(self):
        return '%s(%s, %s, %s)' % (self.__class__.__name__, repr(self.country), repr(self.city), repr(self.name))

    def __eq__(self, other):
        if not isinstance(other, Location):
            return False

        if (self.city is not None and self.city == other.city) or self._not_too_far(other):
            if self.name is not None and self.name == other.name:
                return True

        return None


class Stop(Address):
    ifopt = Field(str)
    uic = Field(str)
    name = Field(str)
    # rides = fields.Model('Ride.Results')
    # lines = fields.Model('Line.Results')

    def __init__(self, country=None, city=None, name=None, **kwargs):
        super().__init__(country=country, city=city, name=name, **kwargs)

    def __repr__(self):
        return '<Stop %s>' % repr(self.full_name if self.full_name else (self.city, self.name))

    def __eq__(self, other):
        if not isinstance(other, Stop):
            return False

        if (self.full_name is not None and other.full_name is not None and
                self.full_name.replace(',', '') == other.full_name.replace(',', '')):
            return True

        if self.city is not None and other.city is not None:
            if self.city.split(' ')[0].lower() != other.city.split(' ')[0].lower():
                return False

            if self.city.startswith(other.city) and other.city.startswith(self.city):
                return self.name == other.name

        return None


class POI(Address):
    name = Field(str)

    def __init__(self, country=None, city=None, name=None, **kwargs):
        super().__init__(country=country, city=city, name=name, **kwargs)

    def __eq__(self, other):
        if not isinstance(other, POI):
            return False

        return super().__eq__(other)
