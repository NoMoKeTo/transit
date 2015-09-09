#!/usr/bin/env python3
from collections import OrderedDict
from . import fields
import copy


class MetaSerializable(type):
    def __new__(mcs, name, bases, attrs):
        class_ = super(MetaSerializable, mcs).__new__(mcs, name, bases, attrs)
        class_._fields = OrderedDict()
        for base in class_.__bases__:
            if base != object:
                class_._fields.update(base._fields)
        class_._fields.update(OrderedDict(sorted(
            [(n, v) for n, v in attrs.items() if isinstance(v, fields.Field)],
            key=lambda v: v[1].i)
        ))
        return class_

    def __init__(cls, name, bases, attrs):
        if name not in ('Request', 'Results', 'Result'):
            fields.Model.add_model(cls)


class Serializable(metaclass=MetaSerializable):
    _fields = OrderedDict()

    def __init__(self, *args, **kwargs):
        self.serialize = self._serialize_instance
        for name, field in self.__class__._fields.items():
            if name in kwargs and (field.none or kwargs[name] is not None):
                setattr(self, name, kwargs[name])
            else:
                setattr(self, name, field.get_default())

    def validate(self):
        for name, field in self._fields.items():
            if not field.validate(getattr(self, name)):
                return False
        return True

    @classmethod
    def serialize(cls, obj, **kwargs):
        assert isinstance(obj, cls)
        if obj.__class__ is cls:
            return obj.serialize(**kwargs)
        else:
            return [obj.__class__._serialized_name(), obj.serialize(**kwargs)]

    def _serialize_instance(self, exclude=[], **kwargs):
        self.validate()

        data = [((name[1:] if name.startswith('_') else name), field.serialize(getattr(self, name), **kwargs))
                for name, field in self._fields.items() if name not in exclude]
        return OrderedDict((n, v) for n, v in data if v is not None)

    @classmethod
    def unserialize(cls, data):
        if isinstance(data, list) and len(data) == 2:
            model_, data = data
            assert model_ in fields.Model._models
            cls_ = fields.Model._models[model_]
            assert issubclass(cls_, cls)
            return cls_.unserialize(data)
        assert isinstance(data, (dict, OrderedDict))
        kwargs = {}
        for name, field in cls._fields.items():
            n = name[1:] if name.startswith('_') else name
            if n in data:
                kwargs[name] = field.unserialize(data[n])

        if issubclass(cls, Searchable.Results):
            return cls(scored=True, **kwargs)
        else:
            return cls(**kwargs)

    @classmethod
    def _serialized_name(cls):
        if hasattr(cls, 'Model'):
            return cls.Model.__name__ + '.' + cls.__name__
        else:
            return cls.__name__

    def __ne__(self, other):
        compared = self == other
        if compared is None:
            return None
        return not compared

    def apply_recursive(self, **kwargs):
        for name, field in self.__class__._fields.items():
            value = getattr(self, name)

            newvalue = field.apply_recursive(value, **kwargs)
            if newvalue is not None:
                setattr(self, name, newvalue)

    def update(self, other):
        if other.__class__ != self.__class__:
            raise ValueError

        for name, field in self.__class__._fields.items():
            myvalue = getattr(self, name)
            if myvalue is None:
                othervalue = getattr(other, name)
                if othervalue is not None:
                    setattr(self, name, othervalue)


class MetaSearchable(MetaSerializable):
    def __new__(mcs, name, bases, attrs):
        if 'Request' not in attrs:
            attrs['Request'] = type('Request', (bases[0].Request,), {'__module__': attrs['__init__'].__module__})
        if 'Results' not in attrs:
            attrs['Results'] = type('Results', (bases[0].Results,), {'__module__': attrs['__init__'].__module__})

        return super(MetaSearchable, mcs).__new__(mcs, name, bases, attrs)

    def __init__(cls, name, bases, attrs):
        cls.Request.Model = cls
        cls.Results.Model = cls
        fields.Model.add_model(cls.Request)
        fields.Model.add_model(cls.Results)
        if name != 'Ride':
            cls.Results._fields['results'] = fields.List(fields.Tuple(fields.Model(cls), fields.Field(int)))
        MetaSerializable.__init__(cls, name, bases, attrs)


class MetaSearchableInner(MetaSerializable):
    def __repr__(cls):
        return repr(cls.Model)[:-2] + '.' + cls.__name__ + "'>"


class Searchable(Serializable, metaclass=MetaSearchable):
    def matches(self, request):
        if not isinstance(request, Searchable.Request):
            raise TypeError('not a request')
        return request.matches(self)

    class Request(Serializable, metaclass=MetaSearchableInner):
        limit = fields.Field(int)

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.limit = None

        def matches(self, obj):
            if not isinstance(obj, self.Model):
                raise TypeError('%s.Request can only match %s' % (self.Model.__name__, self.Model.__name__))
            obj.validate()
            return self._matches(obj)

        def _matches(self, obj):
            pass

    class Results(Serializable, metaclass=MetaSearchableInner):
        def __init__(self, results=[], scored=False, **kwargs):
            results = list(results) if scored else [(r, None) for r in results]
            super().__init__(results=results, **kwargs)

        def filter(self, request):
            if not self.results:
                return

            if not isinstance(request, self.Model.Request):
                raise TypeError('%s.Results can be filtered with %s' % (self.Model.__name__, self.Model.__name__))

            self.results = [r for r in self.results if request.matches(r)]

        def filtered(self, request):
            obj = copy.copy(self)
            obj.filter(request)
            return obj

        def __iter__(self):
            yield from (r[0] for r in self.results)

        def __len__(self):
            return len(self.results)

        def scored(self):
            yield from self.results

        def append(self, obj, score=None):
            self.results.append((obj, score))

        def __getitem__(self, key):
            return self.results[key]


class NetworkID(Serializable):
    pass


class Collectable(Searchable):
    id = fields.Any()
    source = fields.Field(str, none=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _same_by_id(self, other):
        if self.source is None or other.source is None or self.source != other.source:
            return None

        if self.id is None or other.id is None:
            return None

        return self.id == other.id

    def apply_recursive(self, **kwargs):
        if 'source' in kwargs:
            self.source = kwargs['source']

        super().apply_recursive(**kwargs)

        collect = kwargs.get('collect')
        if collect is not None and self.id is not None and self.source is not None:
            myid = (self._serialized_name(), self.source, self.id)
            replace_with = collect.get(myid)
            if replace_with is None:
                collect[myid] = self
            else:
                replace_with.update(self)
                return replace_with


class TripPart(Serializable):
    pass
