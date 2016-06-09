class API:
    StopQuery = None
    TripQuery = None

    def __init__(self, name):
        if self.__class__ == API:
            raise TypeError('Only API subclasses can be initialized.')
        self.name = name

    @property
    def stops(self):
        if self.StopQuery is None:
            raise NotImplementedError('Querying stops is not supported by this network.')
        return self.StopQuery(self)

    @property
    def trips(self):
        if self.TripQuery is None:
            raise NotImplementedError('Querying trips is not supported by this network.')
        return self.TripQuery(self)


class Parser:
    def __init__(self, parent, data, *args, **kwargs):
        self.network = parent.network
        self.time = parent.time
        self.data = data
        self._args = args
        self._kwargs = kwargs


class XMLParser(Parser):
    pass


class JSONParser(Parser):
    pass


class parser_property(object):
    def __init__(self, func, name=None):
        self.func = func
        self.name = name or func.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        field = obj.Model._fields[self.name]
        value = obj.__dict__[self.name] = self.func(obj, obj.data, *obj._args, **obj._kwargs)

        if not field.validate(value):
            raise TypeError('Invalid type for attribute %s.' % self.name)

        return value

    def __set__(self, obj, value):
        raise AttributeError("can't set a parser property")

    def __delete__(self, obj):
        raise AttributeError("can't delete a parser property")
