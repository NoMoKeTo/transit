from ....models import Stop, Location, POI, Address
from ....models.base import choo_property
from ....types import Coordinates


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
