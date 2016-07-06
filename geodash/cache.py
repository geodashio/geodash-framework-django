from pymemcache.client.base import Client

from django.conf import settings

try:
    import simplejson as json
except ImportError:
    import json


def geodash_serializer(key, value):
    if type(value) == str:
        return value, 1
    return json.dumps(value), 2


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
