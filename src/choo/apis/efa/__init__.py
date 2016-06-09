from ..base import API
from .queries import StopQuery
from ...models import Stop, Address, POI
from .models.locations import CityOnlyOdvStop, OdvNameElemPOI, OdvNameElemStop, OdvNameElemAddress

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

    def _parse_location(self, data):
        """ Parse an ODV (OriginDestinationVia) XML node """
        odvtype = data.attrib['type']

        # Place.city
        p = data.find('./itdOdvPlace')
        cityid = None
        if p.attrib['state'] == 'empty':
            city = None
        elif p.attrib['state'] != 'identified':
            if p.attrib['state'] == 'list':
                return 'cities', (CityOnlyOdvStop(self, item) for item in p.find('./odvPlaceElem'))
            return 'none', ()
        else:
            city = p.find('./odvPlaceElem').text

        # Location.name
        n = data.find('./itdOdvName')
        if n.attrib['state'] == 'empty':
            if city is not None:
                return 'cities', (CityOnlyOdvStop(self, city), )
            return 'none', ()

        if n.attrib['state'] == 'identified':
            ne = n.find('./odvNameElem')
            # AnyTypes are used in some EFA instances instead of ODV types
            odvtype = ne.attrib.get('anyType', odvtype)
            return odvtype, (self._parse_location_name(ne, city, cityid, odvtype), )

        if n.attrib['state'] != 'list':
            return 'none', ()

        return 'mixed', (self._parse_location_name(item, city, cityid, odvtype)
                         for item in sorted(n.findall('./odvNameElem'), reverse=True,
                                            key=lambda e: e.attrib.get('matchQuality', 0)))

    def _parse_location_name(self, data, city, cityid, odvtype):
        """ Parses the odvNameElem of an ODV """
        if odvtype == 'stop':
            return OdvNameElemStop(self, data, city)
        elif odvtype == 'poi':
            return OdvNameElemPOI(self, data, city)
        elif odvtype in ('street', 'singlehouse', 'coord', 'address'):
            return OdvNameElemAddress(self, data, city)
        else:
            raise NotImplementedError('Unknown odvtype: %s' % odvtype)
