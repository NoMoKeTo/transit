#!/usr/bin/env python3
from ...models import Searchable
from weakref import WeakValueDictionary


class API():
    def __init__(self, name, dump_raw=False):
        self.name = name
        self.dump_raw = dump_raw

    def query(self, obj):
        if isinstance(obj, Searchable):
            result, now = self._query_get(obj)
        elif isinstance(obj, Searchable.Request):
            result, now = self._query_search(obj.Model, obj)
        else:
            raise TypeError('can only query Searchable or Searchable.Request')

        collect = WeakValueDictionary({})
        newresult = result.apply_recursive(time=now, source=self.name, collect=collect)

        for key, value in collect.items():
            if key[0] == 'Stop':
                self._finalize_stop(value)

        return result if newresult is None else newresult

    def _query_get(self, obj):
        raise NotImplementedError

    def _query_search(self, model, request):
        raise NotImplementedError

    def _finalize_stop(self, stop):
        pass
