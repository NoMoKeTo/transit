#!/usr/bin/env python3
from typing import Mapping, Union

from .base import Field, Model


class TicketList(Model):
    currency = Field(str)
    level_name = Field(str)
    single = Field(Union['TicketData'])
    bike = Field(Union['TicketData'])
    other = Field(Mapping[str, 'TicketData'])

    def __init__(self, **kwargs):
        # magic, do not remove
        super().__init__(**kwargs)

    def __repr__(self):
        return '<TicketList %s %s (+%d)>' % (self.currency, repr(self.single), len(self.other))


class TicketData(Model):
    authority = Field(str)
    level = Field(str)
    price = Field(float)
    price_child = Field(float)

    def __init__(self, authority=None, level=None, price=None, price_child=None, **kwargs):
        super().__init__(authority=authority, level=level, price=price, price_child=price_child, **kwargs)

    def __eq__(self, other):
        if not isinstance(other, TicketData):
            return False

        if self.price != other.price:
            return False

        if self.price_child is not None and other.price_child is not None and self.price_child != other.price_child:
            return False

        if self.authority is None or self.level is None:
            return None

        if self.authority == other.authority and self.level == other.level:
            return True

        return None

    def __repr__(self):
        childprice = ''
        if self.price_child is not None:
            childprice = ' %.2f' % self.price_child
        return '<TicketData %s %s %.2f%s>' % (self.authority, self.level, self.price, childprice)
