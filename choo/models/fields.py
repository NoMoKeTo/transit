#!/usr/bin/env python3
from collections import Iterable
from datetime import datetime, timedelta


class Field():
    _i = 0

    def __init__(self, type_, none=True):
        self.type = type_
        self.i = Field._i
        Field._i += 1
        self.none = none

    def validate(self, value):
        if self.none and value is None:
            return True
        return isinstance(value, self.type)

    def serialize(self, value):
        return value

    def apply_recursive(self, value, **kwargs):
        pass

    def unserialize(self, value):
        if self.none and value is None:
            return None
        assert isinstance(value, self.type)
        return value


class Any(Field):
    def __init__(self, none=True):
        super().__init__(None, none)

    def validate(self, value):
        return True

    def serialize(self, value):
        return value

    def unserialize(self, value):
        return value


class DateTime(Field):
    def __init__(self, none=True):
        super().__init__(None, none)

    def validate(self, value):
        if self.none and value is None:
            return True
        return isinstance(value, datetime)

    def serialize(self, value):
        if self.none and value is None:
            return None
        return value.strftime('%Y-%m-%d %H:%M:%S')

    def unserialize(self, value):
        if self.none and value is None:
            return None
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')


class Timedelta(Field):
    def __init__(self, none=True):
        super().__init__(None, none)

    def validate(self, value):
        if self.none and value is None:
            return True
        return isinstance(value, timedelta)

    def serialize(self, value):
        if self.none and value is None:
            return None
        return int(value.total_seconds())

    def unserialize(self, value):
        if self.none and value is None:
            return None
        return timedelta(seconds=value)


class Model(Field):
    _waiting = {}
    _models = {}

    def __init__(self, type_, none=True):
        super().__init__(type_, none=none)
        if isinstance(type_, str):
            if type_ in Model._models:
                type_ = Model._models[type_]
            else:
                if type_ not in Model._waiting:
                    Model._waiting[type_] = [self]
                else:
                    Model._waiting[type_].append(self)
        self.type = type_

    @classmethod
    def add_model(self, model):
        name_ = model._serialized_name()
        if name_ in Model._models:
            return
        Model._models[name_] = model
        if name_ in Model._waiting:
            for field in Model._waiting[name_]:
                field.type = model
            del Model._waiting[name_]

    def apply_recursive(self, value, **kwargs):
        if value is not None:
            value.apply_recursive(**kwargs)

    def validate(self, value):
        if self.none and value is None:
            return True
        assert isinstance(value, self.type)
        return value.validate()

    def serialize(self, value):
        if self.none and value is None:
            return None
        return self.type.serialize(value)

    def unserialize(self, value):
        if self.none and value is None:
            return None
        return self.type.unserialize(value)


class List(Field):
    def __init__(self, field, none=False, set_=False):
        super().__init__(list, none)
        self.field = field
        self.set = set_

    def validate(self, value):
        if self.none and value is None:
            return True
        assert isinstance(value, Iterable)
        for item in value:
            assert self.field.validate(item)
        return True

    def apply_recursive(self, value, **kwargs):
        for item in value:
            self.field.apply_recursive(item, **kwargs)

    def serialize(self, value):
        if self.none and value is None:
            return None
        return [self.field.serialize(item) for item in value]

    def unserialize(self, value):
        if self.none and value is None:
            return None
        return [self.field.unserialize(item) for item in value]


class Set(List):
    def validate(self, value):
        assert super().validate(value)
        for item in value:
            assert self.field.validate(item)

    def unserialize(self, value):
        if self.none and value is None:
            return None
        return set([self.field.unserialize(item) for item in value])


class Tuple(Field):
    def __init__(self, *types, none=False):
        super().__init__(tuple, none)
        self.types = types

    def validate(self, value):
        if self.none and value is None:
            return True
        assert isinstance(value, tuple)
        assert len(value) == len(self.types)
        for i, type_ in enumerate(self.types):
            assert type_.validate(value[i])
        return True

    def apply_recursive(self, value, **kwargs):
        for i, type_ in enumerate(self.types):
            type_.apply_recursive(value[i], **kwargs)

    def serialize(self, value):
        if self.none and value is None:
            return None
        return [type_.serialize(value[i]) for i, type_ in enumerate(self.types)]

    def unserialize(self, value):
        if self.none and value is None:
            return None
        return tuple(type_.unserialize(value[i]) for i, type_ in enumerate(self.types))


class Dict(Field):
    def __init__(self, key, value, none=True):
        super().__init__(dict, none)
        self.key = key
        self.value = value

    def validate(self, value):
        if self.none and value is None:
            return True
        assert isinstance(value, dict)
        for k, v in value.items():
            assert self.key.validate(k)
            assert self.value.validate(v)
        return True

    def apply_recursive(self, value, **kwargs):
        for k, v in value.items():
            self.key.apply_recursive(k, **kwargs)
            self.value.apply_recursive(v, **kwargs)

    def serialize(self, value):
        if self.none and value is None:
            return None
        return {self.key.serialize(k): self.value.serialize(v) for k, v in value.items()}

    def unserialize(self, value):
        if self.none and value is None:
            return None
        return {self.key.unserialize(k): self.value.unserialize(v) for k, v in value.items()}