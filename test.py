#!/usr/bin/env python3
from choo.networks.de import vrr
from choo.models import Serializable, Stop, Location, Trip
import json

# collection = Collection('test')

bs = Stop(city='essen', name='borbeck süd bf')
bo = Stop(city='essen', name='hbf')
# bo = Stop(city='heidelberg', name='hbf')

trip = Trip.Request()
trip.origin = bs
trip.destination = bo

location = Location.Request()
location.name = 'Borbeck'

vrr.dump_raw = True
result = vrr.query(trip)

# import pprint
# pp = pprint.PrettyPrinter(indent=1)
# pp.pprint(result.serialize())
# print(result.results)
serialized = json.dumps(result.serialize(no_duplicates=[]), indent=2)
print(serialized)
