from ....models import Stop, Location, POI, Address
from ....models.base import choo_property
from ....types import Coordinates


class OdvLocationList:
    def __init__(self, network, xml):
        self.network = network
        self.type, self.generator = self._parse_location(xml)

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
            return OdvNameElemStop(self.network, data, city)
        elif odvtype == 'poi':
            return OdvNameElemPOI(self.network, data, city)
        elif odvtype in ('street', 'singlehouse', 'coord', 'address'):
            return OdvNameElemAddress(self.network, data, city)
        else:
            raise NotImplementedError('Unknown odvtype: %s' % odvtype)

    def __iter__(self):
        yield from self.generator


class CityOnlyOdvStop(Stop.Dynamic):
    def __init__(self, network, xml):
        self.network = network
        self._xml = xml

    @choo_property
    def city(self):
        return self._xml.text


class OdvNameElemLocation(Location.Dynamic):
    def __init__(self, network, xml, city):
        self.network = network
        self._xml = xml
        self._city = city

    @choo_property
    def ids(self):
        myid = self._xml.attrib.get('stopID') or self._xml.attrib.get('id')
        return myid and {self.network.name: myid}

    @choo_property
    def city(self):
        return self._xml.attrib.get('locality', self._city)

    @choo_property
    def name(self):
        return self._xml.attrib.get('objectName', self._xml.text)

    @choo_property
    def coords(self):
        if 'x' not in self._xml.attrib:
            return None
        return Coordinates(float(self._xml.attrib['y']) / 1000000,
                           float(self._xml.attrib['x']) / 1000000)


class OdvNameElemStop(Stop.Dynamic, OdvNameElemLocation):
    pass


class OdvNameElemPOI(POI.Dynamic, OdvNameElemLocation):
    pass


class OdvNameElemAddress(Address.Dynamic, OdvNameElemLocation):
    @choo_property
    def street(self):
        return self._xml.attrib.get('streetName')

    @choo_property
    def number(self):
        return self._xml.attrib.get('buildingNumber') or self._xml.attrib.get('houseNumber')

    @choo_property
    def name(self):
        name = self._xml.attrib.get('objectName', self._xml.text)
        if name is not None:
            return name
        return '%s %s' % (self.street, self.number)
