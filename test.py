#!/usr/bin/env python3
from choo.networks.de import vrn
from choo.models import Serializable, Stop, Location, Trip
import json

# collection = Collection('test')

bs = Stop(city='heidelberg', name='kirchheim/rohrbach')
bo = Stop(city='feudenheim', name='ziethenstr')
# bo = Stop(city='heidelberg', name='hbf')

trip = Trip.Request()
trip.origin = bs
trip.destination = bo

location = Location.Request()
location.name = 'Borbeck'


result = vrn.query(trip)

# import pprint
# pp = pprint.PrettyPrinter(indent=1)
# pp.pprint(result.serialize())
# print(result.results)
serialized = json.dumps(Serializable.serialize(result), indent=2)
print(serialized)
# open('test1.json', 'w').write(serialized)
# unserialized = Serializable.unserialize(json.loads(serialized))
# reserialized = json.dumps(Serializable.serialize(unserialized), indent=2)
# open('test2.json', 'w').write(reserialized)
# print(json.dumps(result.serialize(), indent=2))

# stops = sorted(vrr.collection.known['Stop'], key=lambda s: s.name)

# for trip in result:
#    print(trip)
# result = vrr.get_stop_rides(bs)
# result = vrr.get_stop_rides(bo)
# p = PrettyPrint()
# print(p.formatted(result))
# result.serialize(typed=True)
# serialized = result.serialize(typed=True, children_refer_by='test')
# unserialized = unserialize_typed(serialized)
# serialized2 = unserialized.serialize(typed=True)
# open('out1.json', 'w').write(json.dumps(serialized, indent=2, sort_keys=True))
# open('out2.json', 'w').write(json.dumps(serialized2, indent=2, sort_keys=True))
# print(serialized)
# print(json.dumps(serialized, indent=2))
# print(json.dumps(vrr.collection.serialize(typed=True), indent=2))
