#!/usr/bin/env python3
from .models import Serializable
from . import networks
import json
import argparse

parser = argparse.ArgumentParser(prog='choo')
parser.add_argument('--pretty', action='store_true', help='pretty-print output JSON')
parser.add_argument('network', metavar='network', help='network to use, e.g. vrr', choices=networks.__all__)
parser.add_argument('query', help='any Searchable or Searchable.Request as JSON')
args = parser.parse_args()

network = getattr(networks, args.network)
result = Serializable.serialize(network.query(Serializable.unserialize(json.loads(args.query))))
if args.pretty:
    print(json.dumps(result, indent=2, separators=(',', ': ')))
else:
    print(json.dumps(result, separators=(',', ':')))
