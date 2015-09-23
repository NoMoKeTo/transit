#!/usr/bin/env python3
from ...models import Searchable
from ...models import Location, Stop, POI, Address
from ...models import RidePoint, Platform, LiveTime
from ...models import Trip, Ride, RideSegment, Coordinates, TicketList, TicketData
from ...models import Line, LineType, LineTypes, Way, WayType, WayEvent
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from .base import API
import requests
import re


class EFA(API):
    def __init__(self, name, base_url, preset='de', country_by_id=(), replace_in_full_name={}, **kwargs):
        super().__init__(name, **kwargs)
        self.base_url = base_url
        self.country_by_id = () if country_by_id is None else country_by_id
        self.replace_in_full_name = {}
        if preset == 'de':
            self.replace_in_full_name = {
                ', Hauptbahnhof$': ' Hbf',
                ' Hauptbahnhof$': ' Hbf',
                ' Bahnhof$': '',
                ' Bf$': '',
                ' S$': '',
                ', Hbf%': ' Hbf'
            }
        self.replace_in_full_name.update(replace_in_full_name)

    def _query_get(self, obj):
        if isinstance(obj, Stop):
            result, now = self._request_departures(obj)
            if not isinstance(result, obj.__class__):
                result = None
        else:
            raise NotImplementedError
        return result, now

    def _query_search(self, model, request):
        if model == Location:
            return self._request_stops(request)
        elif model == Trip:
            return self._request_trips(request)
        raise NotImplementedError

    def _finalize_stop(self, stop):
        if stop.full_name is None:
            return

        if stop.name is not None and stop.city is None and stop.full_name.endswith(' '+stop.name):
            stop.city = stop.full_name[:-len(stop.name)].strip()
            if stop.city.endswith(','):
                stop.city = stop.city[:-1]

        stop.full_name = stop.full_name+'$'
        for before, after in self.replace_in_full_name.items():
            stop.full_name = stop.full_name.replace(before, after)
        stop.full_name = stop.full_name.replace('$', '').strip()
        if stop.full_name.endswith(','):
            stop.full_name = stop.full_name[:-1]

        if stop.name is not None and stop.city is not None:
            if stop.full_name == stop.city+' '+stop.name:
                stop.full_name = stop.city+', '+stop.name

        # yes, again. exactly at this position, to not strigger
        if stop.name is not None and stop.city is None and stop.full_name.endswith(' '+stop.name):
            stop.city = stop.full_name[:-len(stop.name)].strip()

    # Internal methods start here

    def _convert_location(self, location, wrap=''):
        """ Convert a Location into POST parameters for the EFA Requests """
        myid = location.id if location.source == self.name else None

        city = location.city
        name = location.name

        if city is None and location.full_name is not None:
            name = location.full_name

        model = location.Model if isinstance(location, Location.Request) else location.__class__

        if name is None:
            if location.lat is not None and location.lon is not None:
                r = {'type': 'coord', 'name': '%.6f:%.6f:WGS84' % (location.lon, location.lat)}
            else:
                r = {'type': 'stop', 'place': city, 'name': ''}
        elif issubclass(model, Stop):
            if myid is not None:
                r = {'type': 'stop', 'place': None, 'name': str(myid)}
            elif location.ifopt is not None and location.country is not None:
                r = {'type': 'stop', 'place': None,
                     'name': '%s:%s:%s' % ((location.country, ) + location.ifopt)}
            else:
                r = {'type': 'stop', 'place': city, 'name': name}
        elif issubclass(model, Address):
            r = {'type': 'address', 'place': city, 'name': name}
        elif issubclass(model, POI):
            if myid is not None:
                r = {'type': 'poiID', 'name': str(myid)}
            else:
                r = {'type': 'poi', 'place': city, 'name': name}
        elif issubclass(model, Location):
            r = {'type': 'any', 'place': city, 'name': name if name else None}
        else:
            raise NotImplementedError

        if r['place'] is None:
            del r['place']

        if wrap:
            r = {wrap % n: v for n, v in r.items()}

        return r

    def _request(self, endpoint, data):
        text = requests.post(self.base_url + endpoint, data=data).text
        if self.dump_raw:
            open('dump.xml', 'w').write(text)
        xml = ET.fromstring(text)
        servernow = datetime.strptime(xml.attrib['now'], '%Y-%m-%dT%H:%M:%S')
        return xml, servernow

    def _request_trips(self, triprequest):
        """ Searches connections/Trips; Returns a SearchResult(Trip) """
        now = datetime.now()

        assert triprequest.walk_speed in ('slow', 'normal', 'fast')

        linetypes = triprequest.linetypes
        if linetypes is None:
            linetypes = LineTypes()

        departure = triprequest.departure
        arrival = triprequest.arrival

        if isinstance(departure, datetime):
            departure = LiveTime(departure)
        if isinstance(arrival, datetime):
            arrival = LiveTime(arrival)

        if departure is not None:
            deparr = 'dep'
            time_ = departure.expected_time
        elif arrival is not None:
            deparr = 'arr'
            time_ = arrival.expected_time
        else:
            deparr = 'dep'
            time_ = now

        max_changes = triprequest.max_changes
        if max_changes is None:
            max_changes = 9

        post = {
            'changeSpeed': triprequest.walk_speed,
            'command': '',
            'coordOutputFormat': 'WGS84',
            'imparedOptionsActive': 1,
            'includedMeans': 'checkbox',
            'itOptionsActive': 1,
            'itdDateDay': time_.day,
            'itdDateMonth': time_.month,
            'itdDateYear': time_.year,
            'itdTimeHour': time_.hour,
            'itdTimeMinute': time_.minute,
            'itdTripDateTimeDepArr': deparr,
            'language': 'de',
            'locationServerActive': 1,
            'maxChanges': max_changes,
            'name_via': '',  # .decode('utf-8').encode('iso-8859-1'),
            'nextDepsPerLeg': 1,
            'place_via': '',  # decode('utf-8').encode('iso-8859-1'),
            'ptOptionsActive': 1,
            'requestID': 0,
            'routeType': 'LEASTTIME',
            # {'speed':'LEASTTIME', 'waittime':'LEASTINTERCHANGE', 'distance':'LEASTWALKING'}[select_interchange_by],
            'sessionID': 0,
            'type_via': 'stop',
            'useRealtime': 1,
            'outputFormat': 'XML'
        }

        # if use_realtime: post['useRealtime'] = 1

        if 'train' in linetypes:
            post['inclMOT_0'] = 'on'

        if 'train.longdistance.highspeed' in linetypes:
            post['lineRestriction'] = 400
        elif 'train.longdistance' in linetypes:
            post['lineRestriction'] = 401
        else:
            post['lineRestriction'] = 403

        for linetype, number in (('urban', '1'), ('metro', '2'), ('metro', '3'),
                                 ('tram', '4'), ('bus.city', '5'), ('bus.regional', '6'),
                                 ('bus.express', '7'), ('suspended', '8'), ('ship', '9'),
                                 ('dialable', '10'), ('other', '11')):
            if linetype in linetypes:
                post['inclMOT_' + number] = 'on'

        if triprequest.wayduration_origin or triprequest.wayduration_destination:
            post['useProxFootSearch'] = 1

        waytypes = {'walk': 100, 'bike': 101, 'car': 104, 'taxi': 105}
        post['trITDepMOT'] = waytypes[str(triprequest.waytype_origin)]
        post['trITArrMOT'] = waytypes[str(triprequest.waytype_destination)]

        post['trITDepMOTvalue%d' % post['trITDepMOT']] = triprequest.wayduration_origin.total_seconds() // 60
        post['trITArrMOTvalue%d' % post['trITArrMOT']] = triprequest.wayduration_destination.total_seconds() // 60

        if triprequest.with_bike:
            post['bikeTakeAlong'] = 1

        if triprequest.wheelchair:
            post['wheelchair'] = 1

        if triprequest.low_floor_only:
            post['lowPlatformVhcl'] = 1

        if not triprequest.allow_solid_stairs:
            post['noSolidStairs'] = 1

        if not triprequest.allow_escalators:
            post['noEscalators'] = 1

        if not triprequest.allow_elevators:
            post['noElevators'] = 1

        post.update(self._convert_location(triprequest.origin, '%s_origin'))
        post.update(self._convert_location(triprequest.destination, '%s_destination'))

        xml, servernow = self._request('XSLT_TRIP_REQUEST2', post)
        data = xml.find('./itdTripRequest')

        results = Trip.Results(self._parse_trips(data.find('./itdItinerary/itdRouteList')))
        results.origin = self._parse_location(data.find('./itdOdv[@usage="origin"]'))
        results.destination = self._parse_location(data.find('./itdOdv[@usage="destination"]'))

        # todo – better exceptions here
        if isinstance(results.origin, list):
            raise ValueError('origin not found')

        if isinstance(results.destination, list):
            raise ValueError('destination not found')

        return results, servernow

    def _request_stops(self, stop):
        """ Searches a Stop; Returns a SearchResult(Stop) """
        post = {
            'language': 'de',
            'outputFormat': 'XML',
            'coordOutputFormat': 'WGS84',
            'locationServerActive': 1,
            # 'regionID_sf': 1, // own region
            'SpEncId': 0,
            'odvSugMacro': 'true',
            'useHouseNumberList': 'true',
        }
        post.update(self._convert_location(stop, '%s_sf'))

        xml, servernow = self._request('XSLT_STOPFINDER_REQUEST', post)
        data = xml.find('./itdStopFinderRequest')

        results = self._parse_location(data.find('./itdOdv'))
        if type(results) != list:
            return stop.Model.Results([results] if isinstance(results, stop.Model) else []), servernow

        results = [result for result in results if isinstance(result[0], stop.Model)]

        if isinstance(stop, Searchable.Request) and stop.limit is not None:
            results = results[:stop.limit]

        return stop.Model.Results(results, scored=True), servernow

    def _request_departures(self, stop: Stop, time=None):
        """ Fills in Stop.rides; Can Return A SearchResult(Stop) without rides. """
        if time is None:
            time = datetime.now()

        post = {
            'command': '',
            'coordOutputFormat': 'WGS84',
            'imparedOptionsActive': 1,
            'itdDateDay': time.day,
            'itdDateMonth': time.month,
            'itdDateYear': time.year,
            'itdTimeHour': time.hour,
            'itdTimeMinute': time.minute,
            'language': 'de',
            'lsShowTrainsExplicit': 1,
            'mode': 'direct',
            'outputFormat': 'XML',
            'locationServerActive': 1,
            'itOptionsActive': 1,
            'ptOptionsActive': 1,
            'includeCompleteStopSeq': 1,
            'depType': 'stopEvents',
            'useRealtime': 1,
            'stateless': 1,
            'requestID': 0,
            'sessionID': 0
        }
        post.update(self._convert_location(stop, '%s_dm'))

        xml, servernow = self._request('XSLT_DM_REQUEST', post)
        data = xml.find('./itdDepartureMonitorRequest')

        stop = self._parse_location(data.find('./itdOdv'))

        if type(stop) == list:
            raise ValueError('Stop not found.')
            # todo return Stop.Results(stop), servernow

        lineslist = data.find('./itdServingLines')

        if lineslist is not None:
            rlines = []
            lines = lineslist.findall('./itdServingLine')
            for line in lines:
                ride, origin, destination = self._parse_ride(line)
                line = ride.line
                line.first_stop = origin
                line.last_stop = destination
                # line.low_quality = True
                rlines.append(line)
            stop.lines = Line.Results(rlines)

        departureslist = data.find('./itdDepartureList')
        stop.rides = self._parse_departures(departureslist, stop, servernow)

        return stop, servernow

    def _parse_stopid_country(self, i):
        for s, country in self.country_by_id:
            if i.startswith(s):
                return country
        return None

    def _get_attrib(self, xml, *keys, noempty=True, default=None, strip=False):
        attrib = xml.attrib
        for key in keys:
            value = attrib.get(key)
            if strip:
                value = value.strip()
            if value or (not noempty and value == ''):
                return value
        return default

    def _parse_stop_line(self, data):
        """ Parse an ODV line (for example an AssignedStop) """
        stop = Stop(country=self._parse_stopid_country(data.attrib['stopID']),
                    name=data.text,
                    city=self._get_attrib(data, 'locality', 'place'),
                    full_name=self._get_attrib(data, 'nameWithPlace'),
                    id=int(data.attrib['stopID']))

        gid = data.attrib.get('gid', '').split(':')
        if len(gid) == 3 and min(len(s) for s in gid):
            stop.country = 'de'
            stop.ifopt = ':'.join((gid[1], gid[2]))

        if 'x' in data.attrib:
            stop.lat = float(data.attrib['y']) / 1000000
            stop.lon = float(data.attrib['x']) / 1000000

        return stop

    def _parse_location(self, data):
        """ Parse an ODV (OriginDestinationVia) XML node """
        odvtype = data.attrib['type']
        results = []

        # Place.city
        p = data.find('./itdOdvPlace')
        cityid = None
        if p.attrib['state'] == 'empty':
            city = None
        elif p.attrib['state'] != 'identified':
            if p.attrib['state'] == 'list':
                pe = p.find('./odvPlaceElem')
                for item in pe:
                    location = Location(None, city=item.text)
                    results.append(location)
            return results
        else:
            pe = p.find('./odvPlaceElem')
            cityid = pe.attrib.get('placeID')
            city = pe.text

        # Location.name
        n = data.find('./itdOdvName')
        if n.attrib['state'] == 'empty':
            if city is not None:
                location = Location(None, city)
                results.append(location)
            return results
        elif n.attrib['state'] != 'identified':
            if n.attrib['state'] == 'list':
                ne = n.findall('./odvNameElem')
                results = [self._parse_location_name(item, city, cityid, odvtype) for item in ne]
                results.sort(key=lambda odv: odv[1], reverse=True)
            return results
        else:
            ne = n.find('./odvNameElem')
            result = self._parse_location_name(ne, city, cityid, odvtype)[0]
            near_stops = []
            for near_stop in data.findall('./itdOdvAssignedStops/itdOdvAssignedStop'):
                stop = self._parse_stop_line(near_stop)
                if stop != result:
                    near_stops.append(stop)
            if near_stops:
                result.near_stops = Stop.Results(near_stops)
            return result

    def _parse_location_name(self, data, city, cityid, odvtype):
        """ Parses the odvNameElem of an ODV """
        # AnyTypes are used in some EFA instances instead of ODV types
        odvtype = self._get_attrib(data, 'anyType', default=odvtype)

        # Even though we got the city, some APIs deliver it only in the odvNameElem…
        city = self._get_attrib(data, 'locality', default=city)

        # What kind of location is it? Fill in attributes.
        name = data.attrib.get('objectName', data.text)
        if odvtype == 'stop':
            location = Stop(city=city, name=name)
        elif odvtype == 'poi':
            location = POI(city=city, name=name)
        elif odvtype == 'street':
            location = Address(city=city, name=name)
        elif odvtype in ('singlehouse', 'coord', 'address'):
            location = Address(city=city, name=name)
            location.street = data.attrib['streetName'] if 'streetName' in data.attrib else None
            location.number = data.attrib['buildingNumber'] if 'buildingNumber' in data.attrib else None
            if location.number is None:
                location.number = data.attrib['houseNumber'] if 'houseNumber' in data.attrib else None
            location.name = '%s %s' % (location.street, location.number)
        else:
            raise NotImplementedError('Unknown odvtype: %s' % odvtype)

        # IDs can come in different ways… Sometimes this is the only way to determine the Location type…
        id_ = self._get_attrib(data, 'stopID', 'id')
        if id_:
            location.country = self._parse_stopid_country(id_)
            location.id = int(id_)

        # This is used when we got more than one Location
        score = int(data.attrib.get('matchQuality', 0))

        # Coordinates
        if 'x' in data.attrib:
            location.lat = float(data.attrib['y']) / 1000000
            location.lon = float(data.attrib['x']) / 1000000

        return location, score

    def _parse_departures(self, data, stop, servernow):
        """ Parses itdDeparture into a List of RideSegment """
        servernow.replace(second=0, microsecond=0)
        results = []
        departures = data.findall('./itdDeparture')
        for departure in departures:
            # Get Line Information
            ride, origin, destination = self._parse_ride(departure.find('./itdServingLine'))

            if departure.find('./genAttrList/genAttrElem[value="HIGHSPEEDTRAIN"]') is not None:
                ride.line.linetype = LineType('train.longdistance.highspeed')
            elif departure.find('./genAttrList/genAttrElem[value="LONG_DISTANCE_TRAINS"]') is not None:
                ride.line.linetype = LineType('train.longdistance')

            # Build Ride Objekt with known stops
            mypoint = self._parse_ridepoint(departure)  # todo: take delay and add it to next stops

            before_delay = after_delay = None
            if mypoint.arrival:
                before_delay = mypoint.arrival.delay
            if mypoint.departure:
                after_delay = mypoint.departure.delay

            delay = None
            if departure.find('./itdServingLine/itdNoTrain'):
                delay = departure.find('./itdServingLine/itdNoTrain').attrib.get('delay', None)
                if delay is not None:
                    delay = timedelta(minutes=delay)

            if delay is not None:
                if ((mypoint.arrival and servernow < mypoint.arrival.expected_time) or
                        (mypoint.departure and servernow < mypoint.departure.expected_time)):
                    before_delay = delay
                else:
                    after_delay = delay

            prevs = False
            for pointdata in departure.findall('./itdPrevStopSeq/itdPoint'):
                point = self._parse_ridepoint(pointdata)
                if point is not None:
                    if before_delay is not None:
                        if (point.arrival is not None and point.arrival.delay is None and
                                point.arrival.time + before_delay >= servernow):
                            point.arrival.delay = before_delay
                        if (point.departure is not None and point.departure.delay is None and
                                point.departure.time + before_delay >= servernow):
                            point.departure.delay = before_delay
                    prevs = True
                    ride.append(point)

            pointer = ride.append(mypoint)

            onwards = False
            for pointdata in departure.findall('./itdOnwardStopSeq/itdPoint'):
                point = self._parse_ridepoint(pointdata)
                if point is not None:
                    if after_delay is not None:
                        if (point.arrival is not None and point.arrival.delay is None and
                                point.arrival.time + after_delay >= servernow):
                            point.arrival.delay = after_delay
                        if (point.departure is not None and point.departure.delay is None and
                                point.departure.time + after_delay >= servernow):
                            point.departure.delay = after_delay
                    onwards = True
                    ride.append(point)

            if not prevs and not onwards:
                ride.prepend(None)
                if origin is not None:
                    ride.prepend(RidePoint(Platform(origin)))

                ride.append(None)
                if destination is not None:
                    ride.append(RidePoint(Platform(destination)))

            # Return RideSegment from the Station we depart from on
            results.append(ride[pointer:])
        return Ride.Results(results)

    def _parse_trips(self, data):
        """ Parses itdRoute into a Trip """
        trips = []
        if data is None:
            return trips

        routes = data.findall('./itdRoute')
        for route in routes:
            trip = Trip()
            interchange = None
            for routepart in route.findall('./itdPartialRouteList/itdPartialRoute'):
                part = self._parse_trippart(routepart)
                if part is None:
                    continue
                if interchange is not None:
                    if isinstance(part, RideSegment):
                        interchange.destination = part[0].platform
                    else:
                        interchange.destination = part[0].origin
                trip._parts.append(part)

                interchange = self._parse_trip_interchange(routepart)
                if isinstance(part, RideSegment):
                    if interchange is not None:
                        interchange.origin = part[-1].platform
                        trip._parts.append(interchange)
                else:
                    if interchange is not None:
                        part.events = interchange.events
                        interchange = None

            ticketlist = TicketList()
            tickets = route.find('./itdFare/itdSingleTicket')
            if tickets:
                authority = tickets.attrib['net']
                ticketlist.single = TicketData(authority,
                                               tickets.attrib['unitsAdult'],
                                               float(tickets.attrib['fareAdult']),
                                               float(tickets.attrib['fareChild']))
                if tickets.get('fareBikeAdult'):
                    ticketlist.bike = TicketData(authority,
                                                 tickets.attrib['unitsBikeAdult'],
                                                 float(tickets.attrib['fareBikeAdult']),
                                                 float(tickets.attrib['fareBikeChild']))
                ticketlist.currency = tickets.attrib['currency']
                ticketlist.level_name = tickets.attrib['unitName']
                for ticket in tickets.findall('./itdGenericTicketList/itdGenericTicketGroup'):
                    t = TicketData()
                    name = ticket.find('./itdGenericTicket[ticket="TICKETTYPE"]/value')
                    if name is None or not name.text:
                        continue

                    authority = ticket.find('./itdGenericTicket[ticket="TARIFF_AUTHORITY"]/value')
                    if authority is not None and authority.text:
                        t.authority = authority.text

                    level = ticket.find('./itdGenericTicket[ticket="FARE_CATEGORY"]/value')
                    if level is not None and level.text:
                        t.level = level.text

                    prices = []
                    adult = ticket.find('./itdGenericTicket[ticket="TICKET_ID_ADULT"]/value')
                    if adult is not None and adult.text:
                        price = ticket.find('./itdGenericTicket[ticket="FARE_ADULT"]/value')
                        if price is not None and price.text:
                            prices.append(float(price.text))

                    child = ticket.find('./itdGenericTicket[ticket="TICKET_ID_CHILD"]/value')
                    if child is not None and child.text:
                        price = ticket.find('./itdGenericTicket[ticket="FARE_CHILD"]/value')
                        if price is not None and price.text:
                            prices.append(float(price.text))

                    if not prices:
                        continue

                    t.price = prices[0]
                    if len(prices) == 2:
                        t.price_child = prices[1]
                    ticketlist.other[name.text] = t
                trip.tickets = ticketlist

            trips.append(trip)

        return trips

    def _parse_trippart(self, data):
        """ Parses itdPartialRoute into a RideSegment or Way """
        points = [self._parse_ridepoint(point) for point in data.findall('./itdPoint')]

        path = []
        for coords in data.findall('./itdPathCoordinates/itdCoordinateBaseElemList/itdCoordinateBaseElem'):
            path.append(Coordinates(float(coords.find('y').text) / 1000000, float(coords.find('x').text) / 1000000))

        motdata = self._parse_ride(data.find('./itdMeansOfTransport'))

        if motdata is None or data.attrib['type'] == 'IT':
            type_ = data.find('./itdMeansOfTransport').attrib['type']
            if type_ == '97':
                # Nicht umsteigen!
                return None
            waytype = {
                '98': 'walk',
                '99': 'walk',
                '100': 'walk',
                '101': 'bike',
                '104': 'car',
                '105': 'taxi'
            }[type_]
            # 98 = gesicherter anschluss

            way = Way(WayType(waytype), points[0].stop, points[1].stop)
            way.distance = data.attrib.get('distance')
            if way.distance is not None:
                way.distance = float(way.distance)
            duration = data.attrib.get('timeMinute', None)
            if duration is not None:
                way.duration = timedelta(minutes=int(duration))
            if path:
                way.path = path
            return way

        else:
            ride, origin, destination = motdata

            if data.find('./genAttrList/genAttrElem[value="HIGHSPEEDTRAIN"]') is not None:
                ride.line.linetype = LineType('train.longdistance.highspeed')
            elif data.find('./genAttrList/genAttrElem[value="LONG_DISTANCE_TRAIN"]') is not None:
                ride.line.linetype = LineType('train.longdistance')

            # Build Ride Objekt with known stops
            for infotext in data.findall('./infoTextList/infoTextListElem'):
                ride.infotexts.append(infotext)

            first = last = None
            waypoints = False
            if data.find('./itdStopSeq'):
                new_points = [self._parse_ridepoint(point)
                              for point in data.findall('./itdStopSeq/itdPoint')]
                if not new_points or new_points[0].stop != new_points[0].stop:
                    new_points.insert(0, points[0])
                if new_points[-1].stop != points[1].stop:
                    new_points.append(points[1])
                points = new_points
                waypoints = True

            first = 0
            last = -1
            for i, p in enumerate(points):
                if i > 0 and not waypoints:
                    ride.append(None)
                ride.append(p)

            if origin is not None:
                if origin != ride[0].stop:
                    ride.prepend(None)
                    ride.prepend(RidePoint(Platform(origin)))
                    first += 2
            else:
                ride.prepend(None)
                first += 1

            if destination is not None:
                if destination != ride[-1].stop:
                    ride.append(None)
                    ride.append(RidePoint(Platform(destination)))
                    last -= 2
            else:
                ride.append(None)
                last -= 1

            segment = ride[first:last]
            segment.set_path(path)
            return segment

    def _parse_trip_interchange(self, data):
        """ Parses an optional interchange path of a itdPartialRoute into a Way """
        info = data.find('./itdFootPathInfo')
        if info is None:
            return None

        way = Way()
        way.duration = timedelta(minutes=int(info.attrib.get('duration')))

        path = []
        for coords in data.findall('./itdInterchangePathCoordinates/itdPathCoordinates'
                                   '/itdCoordinateBaseElemList/itdCoordinateBaseElem'):
            path.append(Coordinates(float(coords.find('y').text) / 1000000, float(coords.find('x').text) / 1000000))

        if path:
            way.path = path

        events = []
        for event in data.findall('./itdFootPathInfo/itdFootPathElem'):
            name = event.attrib['type'].lower()
            direction = event.attrib['level'].lower()
            if name in ('elevator', 'escalator', 'stairs') and direction in ('up', 'down'):
                events.append(WayEvent(name, direction))
        way.events = events

        return way

    def _parse_datetime(self, data):
        """ Create a datetime from itdDate and itdTime """
        d = data.find('./itdDate').attrib
        t = data.find('./itdTime').attrib

        # -1 means nope, there is no time known
        if d['weekday'] == '-1' or d['day'] == '-1' or t['minute'] == '-1':
            return None

        # convert time – the EFA API likes to talk about 24:00, so we have to correct that.
        result = datetime(int(d['year']), int(d['month']), int(d['day']), min(int(t['hour']), 23), int(t['minute']))
        if int(t['hour']) == 24:
            result += timedelta(hours=1)
        return result

    def _parse_ride(self, data):
        """ Parse a itdServingLine Node into something nicer """
        line = Line()
        ride = Ride(line=line)

        if 'motType' not in data.attrib:
            return None

        # determine Type
        mottype = int(data.attrib['motType'])
        line.linetype = LineType(('train.local', 'urban', 'metro', 'urban', 'tram',
                                  'bus.city', 'bus.regional', 'bus.express', 'suspended',
                                  'ship', 'dialable', 'other')[mottype])

        train = data.find('./itdTrain')
        traintype = (train is not None and train.get('type')) or data.attrib.get('trainType')

        if traintype is not None and traintype not in ('RE', 'RB'):
            line.linetype = LineType('train.longdistance.highspeed' if traintype in ('ICE', 'THA', 'TGV')
                                     else 'train.longdistance')

        # general Line and Ride attributes
        diva = data.find('./motDivaParams')
        if diva is not None:
            line.network = diva.attrib['network']
            line.id = ':'.join((diva.attrib['network'], diva.attrib['line'], diva.attrib['supplement'],
                                diva.attrib['direction'], diva.attrib['project']))
            ridedir = diva.attrib['direction'].strip()
            if ridedir:
                ride.direction = ridedir

        ride.number = self._get_attrib(data, 'tC', 'key')
        if line.id is not None and ride.number is not None:
            ride.id = '%s:%s' % (line.id, ride.number)

        op = data.find('./itdOperator')
        if op is not None:
            line.operator = op.find('./name').text

        # We behave different for trains and non-trains
        notrain = data.find('./itdNoTrain')
        if mottype == 0:
            line.name = data.attrib['symbol']
            line.product = self._get_attrib(data, 'trainName', 'productName')

            if not line.product:
                line.product = notrain.attrib['name']

            # overrides the diva one
            ride.number = data.attrib.get('trainNum', ride.number)

            prefix = data.attrib.get('trainType', '')
            line.shortname = (prefix + ride.number) if prefix else line.name

            if not line.shortname:
                train = data.find('./itdTrain')
                if train is not None:
                    line.shortname = train.attrib['type']

            if not line.name:
                line.name = line.shortname
        else:
            line.product = data.attrib.get('productName', '')
            if not line.product:
                line.product = data.find('./itdNoTrain').attrib['name']
            if line.product == 'Fernbus':
                line.linetype = LineType('bus.longdistance')
            line.shortname = data.attrib['symbol']
            line.name = ('%s %s' % (line.product, line.shortname)).strip()

        ride.canceled = (notrain.attrib.get('delay', '') == '-9999') if notrain else None

        # origin and destination
        origin = data.attrib.get('directionFrom')
        origin = Stop(full_name=origin) if origin else None

        destination = self._get_attrib(data, 'destination', 'direction')
        destination = Stop(full_name=destination) if destination else None
        if data.attrib.get('destID', ''):
            destination.country = self._parse_stopid_country(data.attrib['destID'])
            destination.id = int(data.attrib['destID'])

        # route description
        routedescription = data.find('./itdRouteDescText')
        if routedescription is not None:
            line.route = routedescription.text

        return ride, origin, destination

    def _parse_ridepoint(self, data):
        """ Parse a trip Point into a RidePoint (including the Location) """
        city = self._get_attrib(data, 'locality', 'place')
        name = self._get_attrib(data, 'nameWO')
        full_name = self._get_attrib(data, 'name', 'stopName')

        if data.attrib['area'] == '' and data.attrib['stopID'] == '0':
            return None

        location = Stop(country=self._parse_stopid_country(data.attrib['stopID']), city=city,
                        name=name, full_name=full_name)
        location.id = int(data.attrib['stopID'])

        # get and clean the platform
        platform_id = data.attrib['platform'].strip()
        name_platform = platform_id or data.get('platformName')

        match = re.search(r'[0-9].*$', data.attrib['platformName'])
        name_platform = match.group(0) if match is not None else name_platform

        full_platform = data.attrib['platformName'].strip() or name_platform
        if name_platform == full_platform and 'pointType' in data.attrib:
            full_platform = '%s %s' % (data.attrib['pointType'], name_platform)

        platform = Platform(stop=location, name=name_platform, full_name=full_platform)
        if platform_id:
            platform.id = ':'.join((str(location.id), data.attrib['area'], platform_id))

        ifopt = data.attrib.get('gid', '').split(':')
        if len(ifopt) == 3:
            location.country = ifopt[0]
            location.ifopt = ':'.join(ifopt)
            ifopt = data.attrib.get('pointGid', '').split(':')

        if len(ifopt) == 5 and str(location.id).endswith(ifopt[2]):
            if location.ifopt is None:
                location.country = ifopt[0]
                location.ifopt = ':'.join(ifopt[:3])

            if full_platform is not None:
                platform.ifopt = ':'.join(ifopt)

        if data.attrib.get('x'):
            platform.lat = float(data.attrib['y']) / 1000000
            platform.lon = float(data.attrib['x']) / 1000000

        result = RidePoint(platform)
        result.arrival, result.departure, result.passthrough = self._parse_ridepoint_time(data)
        return result

    def _parse_ridepoint_time(self, data):
        # There are three ways to describe the time
        if data.attrib.get('usage', ''):
            # Used for routes (only arrival or departure time)
            times = []
            if data.find('./itdDateTimeTarget'):
                times.append(self._parse_datetime(data.find('./itdDateTimeTarget')))
            if data.find('./itdDateTime'):
                times.append(self._parse_datetime(data.find('./itdDateTime')))

            plantime = None
            expected_time = None
            if len(times) > 0:
                plantime = times[0]
            if len(times) == 2:
                expected_time = times[1]

            if data.attrib['usage'] == 'departure':
                return None, LiveTime(time=plantime, expected_time=expected_time), None
            elif data.attrib['usage'] == 'arrival':
                return LiveTime(time=plantime, expected_time=expected_time), None, None

        elif 'countdown' in data.attrib:
            # Used for departure lists
            times = []
            if data.find('./itdDateTime'):
                times.append(self._parse_datetime(data.find('./itdDateTime')))
            if data.find('./itdRTDateTime'):
                times.append(self._parse_datetime(data.find('./itdRTDateTime')))

            plantime = expected_time = None
            if len(times) > 0:
                plantime = times[0]
            if len(times) == 2:
                expected_time = times[1]
            return None, LiveTime(time=plantime, expected_time=expected_time), None

        else:
            # Also used for routes (arrival and departure time – most times)
            times = []
            for itddatetime in data.findall('./itdDateTime'):
                times.append(self._parse_datetime(itddatetime))

            passthrough = not [t for t in times if t is not None]

            arrival = departure = None
            if len(times) > 0 and times[0] is not None:
                delay = int(data.attrib.get('arrDelay', '-1'))
                delay = timedelta(minutes=delay) if delay >= 0 else None
                arrival = LiveTime(time=times[0], delay=delay)

            if len(times) > 1 and times[1] is not None:
                delay = int(data.attrib.get('depDelay', '-1'))
                delay = timedelta(minutes=delay) if delay >= 0 else None
                departure = LiveTime(time=times[1], delay=delay)

            return arrival, departure, passthrough
