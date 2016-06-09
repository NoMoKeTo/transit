from .... import queries
from ....models import Stop
from ..parsers.locations import OdvLocationList


class StopQuery(queries.StopQuery):
    def _execute(self):
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
        post.update(self.network._convert_location(self, '%s_sf'))

        xml, servernow = self.network._request('XML_STOPFINDER_REQUEST', post)
        data = xml.find('./itdStopFinderRequest')

        results = OdvLocationList(self.network, data.find('./itdOdv'))

        if results.type == 'stop':
            return results

        if results.type == 'mixed':
            return (r for r in results if isinstance(r, Stop))

        return ()
