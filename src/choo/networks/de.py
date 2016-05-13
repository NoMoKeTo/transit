#!/usr/bin/env python3
from .apis.efa import EFA


vrr = EFA('vrr', 'http://app.vrr.de/standard/', preset='de')
vrn = EFA('vrn', 'http://fahrplanauskunft.vrn.de/vrn/', preset='de')
