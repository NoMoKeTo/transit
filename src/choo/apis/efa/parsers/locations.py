from ....models import POI, Address, Location, Stop
from ....models.base import parser_property
from ....types import Coordinates
from ...base import XMLParser


class OdvLocationList(XMLParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type, self.generator = self._parse_location(self.data)

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
                return 'cities', (CityOnlyOdvStop(self, city) for city in p.find('./odvPlaceElem'))
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

    def __iter__(self):
        yield from self.generator


class CityOnlyOdvStop(Stop.XMLParser):
    def __init__(self, network, xml):
        self.network = network
        self._xml = xml

    @parser_property
    def city(self):
        return self._xml.text


class OdvNameElemLocation(Location.XMLParser):
    @parser_property
    def ids(self, data, city):
        myid = data.attrib.get('stopID') or data.attrib.get('id')
        return myid and {self.network.name: myid}

    @parser_property
    def city(self, data, city):
        return data.attrib.get('locality', self._city)

    @parser_property
    def name(self, data, city):
        return data.attrib.get('objectName', data.text)

    @parser_property
    def coords(self, data, city):
        if 'x' not in data.attrib:
            return None
        return Coordinates(float(data.attrib['y']) / 1000000,
                           float(data.attrib['x']) / 1000000)


class OdvNameElemStop(Stop.XMLParser, OdvNameElemLocation):
    pass


class OdvNameElemPOI(POI.XMLParser, OdvNameElemLocation):
    pass


class OdvNameElemAddress(Address.XMLParser, OdvNameElemLocation):
    @parser_property
    def street(self, data, city):
        return data.attrib.get('streetName')

    @parser_property
    def number(self, data, city):
        return data.attrib.get('buildingNumber') or data.attrib.get('houseNumber')

    @parser_property
    def name(self, data, city):
        name = data.attrib.get('objectName', data.text)
        if name is not None:
            return name
        return '%s %s' % (self.street, self.number)
