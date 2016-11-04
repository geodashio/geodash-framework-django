import errno
import re
import yaml
import binascii
import cStringIO
from csv import DictWriter

from socket import error as socket_error

from django.conf import settings
from django.http import Http404
from django.views.generic import View
from django.shortcuts import HttpResponse, render_to_response

try:
    import simplejson as json
except ImportError:
    import json

from geodash.cache import provision_memcached_client
from geodash.utils import extract, grep

class GeoDashDictWriter():

    def __init__(self, output, fields, fallback=""):
        self.output = output
        self.fields = fields
        self.fallback = fallback
        self.delimiter = u","
        self.quote = u'"'
        self.newline = u"\n"

    def writeheader(self):
        self.output = self.output + self.delimiter.join([self.quote+x['label']+self.quote for x in self.fields]) + self.newline

    def writerow(self, rowdict):
        row = [extract(x['path'], rowdict, self.fallback) for x in self.fields]
        #
        row = [unicode(x) for x in row]
        row = [x.replace('"','""') for x in row]
        #
        self.output = self.output + self.delimiter.join([self.quote+x+self.quote for x in row]) + self.newline

    def writerows(self, rowdicts):
        rows = []
        for rowdict in rowdicts:
            rows.append([extract(x['path'], rowdict, self.fallback) for x in self.fields])
        for row in rows:
            #
            row = [unicode(x) for x in row]
            row = [x.replace('"','""') for x in row]
            #
            self.output = self.output + self.delimiter.join([self.quote+x+self.quote for x in row]) + self.newline

    def getvalue(self):
        return self.output


class geodash_data_view(View):

    key = None

    def _build_root(self, request, *args, **kwargs):
        return None

    def _build_key(self, request, *args, **kwargs):
        return self.key

    def _build_columns(self, request, *args, **kwargs):
        raise Exception('geodash_data_view._build_columns should be overwritten.  This API likely does not support CSV.')

    def _build_data(self):
        raise Exception('geodash_data_view._build_data should be overwritten')

    def get(self, request, *args, **kwargs):
        ext_lc = kwargs['extension'].lower();
        ##
        data = None
        if settings.GEODASH_CACHE_DATA:
            client = provision_memcached_client()
            if client:
                key = self._build_key(request, *args, **kwargs)
                print "Checking cache with key ", key

                data = None
                try:
                    data = client.get(key)
                except socket_error as serr:
                    data = None
                    print "Error getting data from in-memory cache."
                    if serr.errno == errno.ECONNREFUSED:
                        print "Memcached is likely not running.  Start memcached with supervisord."
                    raise serr

                if not data:
                    print "Data not found in cache."
                    data = self._build_data(request, *args, **kwargs)
                    if ext_lc == "geodash":
                        data = [int(x) for x in data]
                    try:
                        client.set(key, data)
                    except socket_error as serr:
                        print "Error saving data to in-memory cache."
                        if serr.errno == errno.ECONNREFUSED:
                            print "Memcached is likely not running or the data exceeds memcached item size limit.  Start memcached with supervisord."
                        raise serr
                else:
                    print "Data found in cache."
            else:
                print "Could not connect to memcached client.  Bypassing..."
                data = self._build_data(request, *args, **kwargs)
        else:
            print "Not caching data (settings.geodash_CACHE_DATA set to False)."
            data = self._build_data(request, *args, **kwargs)

        data = grep(
            data,
            request.GET.get('root', None),
            [{'path': k, 'value': v} for k, v in request.GET.iteritems() if k != "root"]
        )

        content = json.dumps(data, default=jdefault)
        content = re.sub(
            settings.GEODASH_REGEX_CLIP_COORDS_PATTERN,
            settings.GEODASH_REGEX_CLIP_COORDS_REPL,
            content,
            flags=re.IGNORECASE)

        if ext_lc == "json":
            return HttpResponse(json.dumps(data, default=jdefault), content_type="application/json")
        elif ext_lc == "yml" or ext_lc == "yaml":
            response = yaml.safe_dump(data, encoding="utf-8", allow_unicode=True, default_flow_style=False)
            return HttpResponse(response, content_type="text/plain")
        elif ext_lc == "csv" or ext_lc == "csv":
            columns = self._build_columns(request, *args, **kwargs)
            writer = GeoDashDictWriter("", columns)
            writer.writeheader()
            writer.writerows(extract(self._build_root(request, *args, **kwargs), data, []))
            response = writer.getvalue()
            return HttpResponse(response, content_type="text/csv")
        elif ext_lc == "geodash":
            response = HttpResponse(content_type='application/octet-stream')
            # Need to do by bytes(bytearray(x)) to properly translate integers to 1 byte each
            # If you do bytes(data) it will give 4 bytes to each integer.
            response.write(bytes(bytearray(data)))
            return response
        else:
            raise Http404("Unknown config format.")


def jdefault(o):
    return o.__dict__
