from ..models import Trip
from .base import Query


class TripQuery(Query):
    Model = Trip
