#!/usr/bin/env python3
from .models import Serializable, Searchable
from socketserver import ThreadingMixIn
from http.server import HTTPServer, BaseHTTPRequestHandler
from . import networks, version
import json
import cgi
import argparse
import gzip


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Server', 'choo/%s %s' % (version, self.version_string()))
        self.send_header('Content-Type', 'text/html;charset=UTF-8')
        self.end_headers()
        self.wfile.write(b'<form method="post">')
        self.wfile.write(b'<h1>choo API</h1>')
        self.wfile.write(b'<textarea name="query" required style="width:400px;height:150px;"></textarea><br>')
        self.wfile.write(b'<select name="network" required><option value="">network...</option>')
        for n in networks.__all__:
            self.wfile.write(('<option value="%s">%s</option>' % (n, n)).encode())
        self.wfile.write(b'</select>')
        self.wfile.write(b'<input type="submit" value="send"> &nbsp;')
        self.wfile.write(b'<input type="checkbox" name="pretty" value="1"> pretty JSON')
        self.wfile.write(b'</form>')
        return

    def do_POST(self):
        try:
            data = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                                    environ={'REQUEST_METHOD': 'POST',
                                             'CONTENT_TYPE': self.headers['Content-Type']})
        except:
            self.send_error(400, message='invalid post data', explain='could not decode')
            self.send_header('Server', 'choo/%s %s' % (version, self.version_string()))
            self.end_headers()
            return
        data = {key: data.getlist(key)[0] for key in data}

        if 'network' not in data:
            self.send_error(400, message='no network', explain='please select a supported network')
            self.send_header('Server', 'choo/%s %s' % (version, self.version_string()))
            self.end_headers()
            return

        if 'query' not in data:
            self.send_error(400, message='no query', explain='please specify a query')
            self.send_header('Server', 'choo/%s %s' % (version, self.version_string()))
            self.end_headers()
            return

        try:
            network = data['network']
            assert network in networks.__all__
            network = getattr(networks, network)
        except:
            self.send_error(404, message='unknown network', explain='you selected an unknown network')
            self.send_header('Server', 'choo/%s %s' % (version, self.version_string()))
            self.end_headers()
            return

        if 'query' not in data:
            self.send_error(400, message='no query', explain='please specify a query')
            self.send_header('Server', 'choo/%s %s' % (version, self.version_string()))
            self.end_headers()
            return

        try:
            query = json.loads(data['query'])
        except:
            self.send_error(400, message='could not unpack', explain='your query is not valid json')
            self.send_header('Server', 'choo/%s %s' % (version, self.version_string()))
            self.end_headers()
            return

        try:
            query = Serializable.unserialize(query)
        except:
            self.send_error(400, message='could not unserialize',
                            explain='your query is not a valid typed serialized choo object')
            self.send_header('Server', 'choo/%s %s' % (version, self.version_string()))
            self.end_headers()
            return

        if not isinstance(query, (Searchable, Searchable.Request)):
            self.send_error(400, message='not searchable',
                            explain='%s is not a Searchable or Searchable.Request' % query._serialized_name())
            self.send_header('Server', 'choo/%s %s' % (version, self.version_string()))
            self.end_headers()
            return

        try:
            result = network.query(query)
        except:
            raise
            self.send_error(500, message='query error', explain='an exception occured during your query')
            self.send_header('Server', 'choo/%s %s' % (version, self.version_string()))
            self.end_headers()
            return

        try:
            result = Serializable.serialize(result)
            if data.get('pretty'):
                result = json.dumps(result, indent=2, separators=(',', ': '))
            else:
                result = json.dumps(result, separators=(',', ':'))
        except:
            self.send_error(500, message='could not serialize', explain='the query result could not be serialized')
            self.send_header('Server', 'choo/%s %s' % (version, self.version_string()))
            self.end_headers()
            return

        do_gzip = 'gzip' in [s.strip() for s in self.headers.get('Accept-Encoding', '').split(',')]

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        if do_gzip:
            self.send_header("Content-Encoding", "gzip")
        self.send_header('Server', 'choo/%s %s' % (version, self.version_string()))
        self.end_headers()

        if do_gzip:
            f = gzip.GzipFile(fileobj=self.wfile, mode='w')
            f.write(result.encode())
            f.close()
        else:
            self.wfile.write(result.encode())
        return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

parser = argparse.ArgumentParser()
parser.add_argument('--host', type=str, default='0.0.0.0', help='set address to listen on (default: 0.0.0.0)')
parser.add_argument('--port', type=int, default=0, help='set tcp port (default: random unused port)')
args = parser.parse_args()

server = ThreadedHTTPServer((args.host, args.port), Handler)
ip, port = server.server_address
print('Starting server on %s:%d' % (ip, port))
server.serve_forever()
