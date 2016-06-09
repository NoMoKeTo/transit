from ..base import API
from .queries import StopQuery


class EFA(API):
    StopQuery = StopQuery
