from typing import Iterable

from ..types import LineType, LiveTime
from .base import Field, Model
from .locations import ModelWithIDs, Platform, Stop


class Line(ModelWithIDs):
    linetype = Field(LineType)
    product = Field(str)
    name = Field(str)
    shortname = Field(str)
    route = Field(str)
    first_stop = Field(Stop)
    last_stop = Field(Stop)
    network = Field(str)
    operator = Field(str)

    def __init__(self, linetype=None, **kwargs):
        super().__init__(linetype=(LineType() if linetype is None else linetype), **kwargs)

        def __repr__(self):
            return '<Line %s %s>' % (str(self.linetype), repr(self.name))


class MetaRide(ModelWithIDs):
    line = Field(Line)
    number = Field(str)
    direction = Field(str)
    bike_friendly = Field(bool)
    annotation = Field(Iterable[str])


class Ride(ModelWithIDs):
    meta = Field(MetaRide)
    canceled = Field(bool)
    infotexts = Field(Iterable[str])


class RidePoint(Model):
    platform = Field(Platform)
    stop = Field(Stop)
    arrival = Field(LiveTime)
    departure = Field(LiveTime)
    passthrough = Field(bool)

    def __init__(self, platform=None, arrival=None, departure=None, **kwargs):
        super().__init__(platform=platform, arrival=arrival, departure=departure, **kwargs)

    def __eq__(self, other):
        if not isinstance(other, RidePoint):
            return False

        sametimes = 0
        if self.arrival is not None and other.arrival is not None:
            if self.arrival != other.arrival:
                return False
            sametimes += 1

        if self.departure is not None and other.departure is not None:
            if self.departure != other.departure:
                return False
            sametimes += 1

        if not sametimes:
            return None

        return self.platform != other.platform

    def __repr__(self):
        return ('<RidePoint %s %s %s>' % (self.arrival, self.departure, self.platform))
