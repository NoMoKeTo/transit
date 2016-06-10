from typing import Union

from ..types import Coordinates, PlatformIFOPT, StopIFOPT
from .base import Field, Model, ModelWithIDs


class GeoPoint(Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    coords = Field(Coordinates)


class Platform(GeoPoint, ModelWithIDs):
    stop = Field(Union['Stop'])
    ifopt = Field(PlatformIFOPT)
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


class City(ModelWithIDs):
    country = Field(str)
    state = Field(str)
    official_id = Field(str)
    name = Field(str)

    def __init__(self, name=None, country=None, **kwargs):
        super().__init__(**kwargs)
        self.country = country
        self.name = name

    def __repr__(self):
        return '<%s: %s, %s, %s>' % (self.__class__.__name__, self.country, self.state, self.name)


class Location(GeoPoint):
    city = Field(City)
    name = Field(str)

    def __init__(self, city=None, name=None, **kwargs):
        super().__init__(**kwargs)
        self.city = city
        self.name = name

    @property
    def country(self):
        return self.city.country if self.city else None

    @property
    def city_name(self):
        return self.city.name if self.city else None

    def __repr__(self):
        return '<%s: %s, %s, %s>' % (self.__class__.__name__, self.country, self.city_name, self.name)


class Address(Location):
    street = Field(str)
    number = Field(str)
    postcode = Field(str)
    # near_stops = fields.Model('Stop.Results')

    def __repr__(self):
        return '<%s: %s-%s %s, %s>' % (self.__class__.__name__, self.country.upper(), self.postcode, self.city_name, self.name)


class Addressable(Location):
    address = Field(Address)


class Stop(Addressable, ModelWithIDs):
    ifopt = Field(StopIFOPT)
    uic = Field(str)
    # rides = fields.Model('Ride.Results')
    # lines = fields.Model('Line.Results')

    def __init__(self, city=None, name=None, **kwargs):
        super().__init__(city=city, name=name, **kwargs)

    @property
    def country(self):
        if self.ifopt:
            return self.ifopt.country
        return self.city.country if self.city else None

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


class POI(Addressable, ModelWithIDs):
    def __init__(self, city=None, name=None, **kwargs):
        super().__init__(city=city, name=name, **kwargs)

    def __eq__(self, other):
        if not isinstance(other, POI):
            return False

        return super().__eq__(other)
