from ..models.base import Field, Model
from collections import ChainMap, OrderedDict
from itertools import chain


class MetaQuery(type):
    def __new__(mcs, name, bases, attrs):
        not_field_attrs = {n: v for n, v in attrs.items() if not isinstance(v, Field)}
        cls = super(MetaQuery, mcs).__new__(mcs, name, bases, not_field_attrs)
        try:
            Model = attrs['Model']
        except KeyError:
            for base in bases:
                if hasattr(base, 'Model'):
                    Model = base.Model
                    break
            else:
                raise TypeError('Query without Model!')

        cls._fields = Model._fields

        cls._settings = OrderedDict()
        for base in cls.__bases__:
            if base != object:
                cls._settings.update(base._settings)
        if '_settings' in attrs:
            cls._settings.update(attrs['_settings'])

        cls._combined = ChainMap(cls._fields, cls._settings)
        return cls


class Query(metaclass=MetaQuery):
    Model = Model
    _settings = {'limit': None}

    def __init__(self, network):
        if self.__class__ == Query:
            raise TypeError('only subclasses of Query can be initialised')

        self.network = network
        self._data = self._settings.copy()
        self._cached_results = []
        self._results_generator = None
        self._results_done = False

    def update(self, **kwargs):
        result = self.__class__(self.network)

        for name, value in kwargs.items():
            try:
                field = self._fields[name]
            except KeyError:
                raise TypeError('invalid field: %s.%s' % (self.Model.__name__, name))

            if not field.validate(value):
                raise TypeError('invalid type for %s.%s: %s' % (self.Model.__name__, name, repr(value)))

            result._data[name] = value

        return result

    def get(self, obj):
        if not isinstance(obj, self.Model):
            raise TypeError('Expected %s instance, got %s' % (self.Model.__name__, repr(obj)))

        r = self.update(**{name: getattr(obj, name, None) for name in self._fields}).setlimit(1).execute()
        if not r:
            raise self.Model.NotFound
        return next(iter(r))

    def _execute(self, obj):
        raise TypeError('Cannot execute query not bound to a network')

    def setlimit(self, limit):
        if limit is not None and (not isinstance(limit, int) or limit < 1):
            raise TypeError('limit has to be None or int > 1')
        self._data['limit'] = limit
        return self

    def execute(self):
        if self._results_generator is None:
            self._results_generator = self._execute()
        return self

    def __iter__(self):
        self.execute()

        if self._results_done:
            return iter(self._cached_results)

        return chain(self._cached_results, self._next_result())

    def _next_result(self):
        for result in self._results_generator:
            self._cached_results.append(result)
            yield result
        self._results_done = True

    def __getattr__(self, name):
        if name not in self._combined:
            raise AttributeError

        try:
            return self._data[name]
        except KeyError:
            pass
        raise AttributeError('%s.%s is currently not set on this query.')

    def __setattr__(self, name, value):
        if name in self._combined:
            raise TypeError('Can not set fields, use .update()!')
        super().__setattr__(name, value)
