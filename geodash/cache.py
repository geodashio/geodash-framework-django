import decimal

from pymemcache.client.base import Client

from django.conf import settings

try:
    import simplejson as json
except ImportError:
    import json


class DecimalEncoder(json.JSONEncoder):
    def _iterencode(self, o, markers=None):
        if isinstance(o, decimal.Decimal):
            return (str(o) for o in [o])
        return super(self.__class__, self)._iterencode(o, markers)

def geodash_serializer(key, value):
    if type(value) == str:
        return value, 1
    return json.dumps(value, cls=DecimalEncoder), 2


def geodash_deserializer(key, value, flags):
    if flags == 1:
        return value
    elif flags == 2:
        return json.loads(value)
    else:
        raise Exception("Unknown serialization format")

def provision_memcached_client():
    client = Client(
        (settings.GEODASH_MEMCACHED_HOST, settings.GEODASH_MEMCACHED_PORT),
        serializer=geodash_serializer,
        deserializer=geodash_deserializer)
    return client
