from collections import OrderedDict
from ..exceptions import ObjectNotFound
from typing import Mapping, Union, Iterable, Optional


class Field:
    """
    A field on a Choo Model
    """
    _i = 0

    def __init__(self, types):
        self.types = Optional[types]
        self.i = Field._i
        Field._i += 1

    def set_model_and_name(self, model, name):
        self.model = model
        self.name = name
        return self

    def validate(self, value):
        return issubclass(type(value), self.types)

    def __get__(self, obj, cls):
        if obj is None:
            return self
        try:
            return obj._data[self.name]
        except KeyError:
            raise AttributeError('Attribute %s is not set.' % self.name)

    def __set__(self, obj, value):
        if not self.validate(value):
            raise TypeError('Invalid type for attribute %s.' % self.name)
        obj._data[self.name] = value

    def __delete__(self, obj):
        try:
            del obj._data[self.name]
        except KeyError:
            raise AttributeError('Attribute %s is not set.' % self.name)


class choo_property(object):
    def __init__(self, func, name=None):
        self.func = func
        self.name = name or func.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        field = obj.Model._fields[self.name]
        value = obj.__dict__[self.name] = self.func(obj)

        if not field.validate(value):
            raise TypeError('Invalid type for attribute %s.' % self.name)

        return value

    def __set__(self, obj, value):
        raise AttributeError("can't set a choo property")

    def __delete__(self, obj):
        raise AttributeError("can't delete a choo property")


def give_none(self):
    return None


class DynamicModel:
    def __init__(self):
        pass


class MetaModel(type):
    def __new__(mcs, name, bases, attrs):
        cls = super(MetaModel, mcs).__new__(mcs, name, bases, attrs)
        cls.NotFound = type('NotFound', (ObjectNotFound, ), {'__module__': attrs['__module__']})
        cls._fields = OrderedDict()
        for base in cls.__bases__:
            cls._fields.update(getattr(base, '_fields', {}))

        cls._fields.update(OrderedDict(sorted(
            [(n, v.set_model_and_name(cls, n)) for n, v in attrs.items() if isinstance(v, Field)],
            key=lambda v: v[1].i)
        ))

        if issubclass(cls, DynamicModel):
            for name in cls._fields:
                if not hasattr(cls, name):
                    setattr(cls, name, choo_property(give_none, name))
        else:
            cls.Dynamic = type('Dynamic', (DynamicModel, ), {'__module__': attrs['__module__'], 'Model': cls})
        return cls


class Model(metaclass=MetaModel):
    def __init__(self):
        self._data = {}

    def serialize(self, exclude=[], **kwargs):
        data = [('type', self._serialized_name())]
        for name, field in self._fields.items():
            try:
                val = self._data[name]
            except KeyError:
                continue
            data = (name, val if isinstance([int, float, str, dict, list]) else val.serialize())
        return OrderedDict(data)


class ModelWithIDs(Model):
    ids = Field(Mapping[str, Union[str, Iterable[str]]])
