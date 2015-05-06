#!/usr/bin/env python3
from .locations import Coordinates, Stop, Location, Address, POI
from .line import Line, LineType, LineTypes
from .trip import Trip
from .ride import Ride, RideSegment
from .way import Way
from .timeandplace import TimeAndPlace, Platform
from .realtime import RealtimeTime


def unserialize_typed(data):
    model, data = data
    if '.' in model:
        model = model.split('.')
        return getattr(globals()[model[0]], model[1]).unserialize(data)
    else:
        return globals()[model].unserialize(data)

__all__ = ['Coordinates', 'Location', 'Stop', 'Address', 'POI', 'Line',
           'LineType', 'LineTypes', 'RealtimeTime', 'TimeAndPlace', 'Platform',
           'Ride', 'RideSegment', 'Trip', 'Way', 'unserialize_typed']