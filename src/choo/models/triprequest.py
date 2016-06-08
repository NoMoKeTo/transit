from datetime import datetime, timedelta
from typing import Iterable

from ..types import LineTypes, WayType
from .base import Field, Model
from .locations import Location


class Request(Model):
    walk_speed = Field(str)
    origin = Field(Location)
    via = Field(Iterable[Location])
    destination = Field(Location)
    departure = Field(datetime)
    arrival = Field(datetime)
    linetypes = Field(LineTypes)
    max_changes = Field(int)

    with_bike = Field(bool)
    wheelchair = Field(bool)
    low_floor_only = Field(bool)
    allow_solid_stairs = Field(bool)
    allow_escalators = Field(bool)
    allow_elevators = Field(bool)

    waytype_origin = Field(WayType)
    waytype_via = Field(WayType)
    waytype_destination = Field(WayType)

    wayduration_origin = Field(timedelta)
    wayduration_via = Field(timedelta)
    wayduration_destination = Field(timedelta)
