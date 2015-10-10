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

    def serialize(self, exclude=[], **kwargs):
        self.validate()

        data = [('type', self._serialized_name())]
        data += [((name[1:] if name.startswith('_') else name), field.serialize(getattr(self, name), **kwargs))
                 for name, field in self._fields.items() if name not in exclude]
        return OrderedDict((n, v) for n, v in data if v is not None)

    @classmethod
    def unserialize(cls, data):
        assert isinstance(data, (dict, OrderedDict))

        type_ = data.get('type')
        if type_ is not None and type_ != cls._serialized_name():
            assert type_ in fields.Model._models
            cls_ = fields.Model._models[type_]
            assert issubclass(cls_, cls)
            return cls_.unserialize(data)

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
        if 'Result' not in attrs:
            attrs['Result'] = type('Result', (bases[0].Result,), {'__module__': attrs['__init__'].__module__})

        return super(MetaSearchable, mcs).__new__(mcs, name, bases, attrs)

    def __init__(cls, name, bases, attrs):
        cls.Request.Model = cls
        cls.Results.Model = cls
        cls.Result.Model = cls
        fields.Model.add_model(cls.Request)
        fields.Model.add_model(cls.Results)
        fields.Model.add_model(cls.Result)
        cls.Results._fields['results'] = fields.List(fields.Model(cls.Result))
        if cls.__name__ == 'Ride':
            cls.Result._fields['result'] = fields.Model('RideSegment', none=False)
        else:
            cls.Result._fields['result'] = fields.Model(cls, none=False)
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
        def __init__(self, results=[], **kwargs):
            results = [(r if isinstance(r, self.Model.Result) else self.Model.Result(r)) for r in results]
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
            yield from self.results

        def __len__(self):
            return len(self.results)

        def append(self, obj, score=None):
            if isinstance(obj, self.Model):
                self.results.append(self.Result(obj))
            elif isinstance(obj, self.Result):
                self.results.append(obj)
            else:
                raise AssertionError('Can only append compatible types!')

        def __getitem__(self, key):
            return self.results[key]

    class Result(Serializable, metaclass=MetaSearchableInner):
        def __init__(self, result=None, **kwargs):
            super().__init__(result=result, **kwargs)

        def serialize(self, **kwargs):
            me = super().serialize(**kwargs)
            result = me['result']
            del me['result']
            del me['type']
            result.update(OrderedDict(('@%s' % name, value) for name, value in me.items()))
            return result

        @classmethod
        def unserialize(cls, data):
            props = cls._fields.keys()
            result = {name: value for name, value in data.items() if name[1:] not in props}

            newdata = {name[1:]: value for name, value in data.items() if name[1:] in props}
            if data['type'] == 'RideSegment':
                newdata['type'] = 'Ride.Result'
            else:
                newdata['type'] = data['type'].replace('RideSegment', 'Ride')+'.Result'
            newdata['result'] = result

            return super(Searchable.Result, cls).unserialize(newdata)


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
    def __init__(self, **kwargs):
        if self.__class__ == TripPart:
            raise RuntimeError('Only instances of TripPart subclasses are allowed!')
        super().__init__(**kwargs)
