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
