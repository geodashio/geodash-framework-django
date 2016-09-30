import errno
import re
import yaml
import binascii

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


class geodash_data_view(View):

    key = None

    def _build_key(self, request, *args, **kwargs):
        return self.key

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
