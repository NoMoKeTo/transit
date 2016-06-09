from collections import OrderedDict


class Field:
    """
    A field on a Choo Model
    """
    _i = 0

    def __init__(self, types):
        self.types = types
        self.i = Field._i
        Field._i += 1

    def set_model_and_name(self, model, name):
        self.model = model
        self.name = name
        return self

    def __get__(self, obj, cls):
        if obj is None:
            return self
        try:
            return obj._data[self.name]
        except KeyError:
            raise AttributeError('Attribute %s is not set.' % self.name)

    def __set__(self, obj, value):
        if not issubclass(type(value), self.types):
            raise TypeError('Invalid type for attribute %s.' % self.name)
        obj._data[self.name] = value

    def __delete__(self, obj):
        try:
            del obj._data[self.name]
        except KeyError:
            raise AttributeError('Attribute %s is not set.' % self.name)


class choo_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        name = self.func.__name__
        types = getattr(obj.__bases__[0], name).types
        value = obj.__dict__[name] = self.func(obj)

        if not issubclass(type(value), types):
            raise TypeError('Invalid type for attribute %s.' % self.name)

        return value

    def __set__(self, obj, value):
        raise AttributeError("can't set a choo property")

    def __delete__(self, obj):
        raise AttributeError("can't delete a choo property")


class MetaModel(type):
    def __new__(mcs, name, bases, attrs):
        cls = super(MetaModel, mcs).__new__(mcs, name, bases, attrs)
        cls._fields = OrderedDict()
        for base in cls.__bases__:
            if base != object:
                cls._fields.update(base._fields)
        cls._fields.update(OrderedDict(sorted(
            [(n, v.set_model_and_name(cls, n)) for n, v in attrs.items() if isinstance(v, Field)],
            key=lambda v: v[1].i)
        ))
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
