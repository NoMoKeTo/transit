from ..base import API
from .queries import StopQuery
from ...models import Stop, Address, POI

import requests
from datetime import datetime
import os
import pprint
import defusedxml.ElementTree as ET


class EFA(API):
    StopQuery = StopQuery

    def __init__(self, name, base_url):
        super().__init__(name)
        self.base_url = base_url

    def _request(self, endpoint, data):
        if os.environ.get('CHOO_DEBUG'):
            pprint.pprint(data)
        result = requests.post(self.base_url + endpoint, data=data).text
        if os.environ.get('CHOO_DEBUG'):
            open('dump.xml', 'w').write(result)
        xml = ET.fromstring(result)
        servernow = datetime.strptime(xml.attrib['now'], '%Y-%m-%dT%H:%M:%S')
        return xml, servernow

    def _convert_location(self, location, wrap=''):
        """ Convert a Location into POST parameters for the EFA Requests """
        r = None
        if isinstance(location, Stop) or isinstance(location, StopQuery):
            if location.ids and self.name in location.ids:
                r = {'type': 'stop', 'place': None, 'name': str(location.ids[self.name])}
            elif location.ifopt:
                r = {'type': 'stop', 'place': None, 'name': '%s:%s:%s' % location.ifopt}
            else:
                r = {'type': 'stop', 'place': location.city, 'name': location.name}
        elif isinstance(location, POI):
            if location.ids and self.name in location.ids:
                r = {'type': 'poiID', 'name': str(location.ids[self.name])}
            else:
                r = {'type': 'poi', 'place': location.city, 'name': location.name}

        if r is None and isinstance(location, Address):
            r = {'type': 'address', 'place': location.city, 'name': location.address}

        if r is None and location.coords:
            r = {'type': 'coord', 'name': '%.6f:%.6f:WGS84' % (location.coords.lon, location.coords.lat)}

        if r is None:
            raise NotImplementedError('#todo')

        if r['place'] is None:
            del r['place']

        if wrap:
            r = {wrap % n: v for n, v in r.items()}

        return r
