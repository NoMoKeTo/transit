#!/usr/bin/env python3
from .base import Serializable
from .locations import Platform
from . import fields
from datetime import datetime, timedelta


class LiveTime(Serializable):
    time = fields.DateTime(none=False)
    delay = fields.Timedelta()

    def __init__(self, time=None, delay=None, expected_time=None, **kwargs):
        if expected_time is not None:
            if time is None:
                time = expected_time - delay
            elif delay is None:
                delay = expected_time - time
            else:
                assert expected_time - time == delay

        super().__init__(time=time, delay=delay, **kwargs)

    def __repr__(self):
        return '<LiveTime %s>' % (str(self))

    def __str__(self):
        out = self.time.strftime('%Y-%m-%d %H:%M')
        if self.delay is not None:
            out += ' %+d' % (self.delay.total_seconds() / 60)
        return out

    @property
    def is_live(self):
        return self.delay is not None

    @property
    def expected_time(self):
        if self.delay is not None:
            return self.time + self.delay
        else:
            return self.time

    def __add__(self, other):
        assert isinstance(other, timedelta)
        return LiveTime(self.time + other, self.delay)

    def __sub__(self, other):
        assert isinstance(other, timedelta)
        return LiveTime(self.time - other, self.delay)

    def __eq__(self, other):
        if isinstance(other, datetime):
            return self.expected_time == other
        elif isinstance(other, LiveTime):
            return self.time == other.time
        return False

    def __lt__(self, other):
        assert isinstance(other, LiveTime) or isinstance(other, datetime)
        if isinstance(other, datetime):
            return self.expected_time < other
        else:
            return self.expected_time < other.expected_time

    def __gt__(self, other):
        assert isinstance(other, LiveTime) or isinstance(other, datetime)
        if isinstance(other, datetime):
            return self.expected_time < other
        else:
            return self.expected_time < other.expected_time


class RidePoint(Serializable):
    platform = fields.Model(Platform, none=False)
    arrival = fields.Model(LiveTime)
    departure = fields.Model(LiveTime)
    passthrough = fields.Field(bool)

    def __init__(self, platform=None, arrival=None, departure=None, **kwargs):
        super().__init__(platform=platform, arrival=arrival, departure=departure, **kwargs)

    @property
    def stop(self):
        return self.platform.stop

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
