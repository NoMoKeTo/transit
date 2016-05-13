#!/usr/bin/env python3
from .base import Serializable
from . import fields


class TicketList(Serializable):
    currency = fields.Field(str, none=False)
    level_name = fields.Field(str)
    single = fields.Model('TicketData', none=False)
    bike = fields.Model('TicketData')
    other = fields.Dict(fields.Field(str), fields.Model('TicketData'), none=False)

    def __init__(self, **kwargs):
        # magic, do not remove
        super().__init__(**kwargs)

    def __repr__(self):
        return '<TicketList %s %s (+%d)>' % (self.currency, repr(self.single), len(self.other))


class TicketData(Serializable):
    authority = fields.Field(str)
    level = fields.Field(str)
    price = fields.Field(float, none=False)
    price_child = fields.Field(float)

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
