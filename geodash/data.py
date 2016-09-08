import errno
import psycopg2

from socket import error as socket_error

from django.conf import settings
from django.template.loader import get_template

from geodash.enumerations import MONTHS_SHORT3

from geodash.cache import provision_memcached_client


class data_local_country(object):

    key = None

    def _build_key(self, *args, **kwargs):
        raise NotImplementedError

    def _build_data(self, *args, **kwargs):
        raise NotImplementedError

    def get(self, *args, **kwargs):
        data = None
        if settings.GEODASH_CACHE_DATA:
            client = provision_memcached_client()
            if client:
                key = self._build_key(*args, **kwargs)
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
                    data = self._build_data(*args, **kwargs)
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
                data = self._build_data(*args, **kwargs)
        else:
            print "Not caching data (settings.GEODASH_CACHE_DATA set to False)."
            data = self._build_data(*args, **kwargs)

        return data


def calc_breaks_natural(values, n_classes):
    natural = None
    if values:
        from jenks import jenks  # noqa
        natural = [float(bp) for bp in jenks(values, n_classes)]
    else:
        natural = []
    return natural


def valuesByMonthToList(values, nodata="0"):
    return [float(values.get(x, nodata)) for x in MONTHS_SHORT3]


def rowsToDict(rows, keys):
    rowsAsDict = {}
    if keys == 1:
        for row in rows:
            keyA, values = row
            rowsAsDict[keyA] = values
    elif keys == 2:
        for row in rows:
            keyA, keyB, values = row
            if keyA not in rowsAsDict:
                rowsAsDict[keyA] = {}
            rowsAsDict[keyA][keyB] = values
    elif keys == 3:
        for row in rows:
            keyA, keyB, keyC, values = row
            if keyA not in rowsAsDict:
                rowsAsDict[keyA] = {}
            if keyB not in rowsAsDict[keyA]:
                rowsAsDict[keyA][keyB] = {}
            rowsAsDict[keyA][keyB][keyC] = values
    return rowsAsDict


def assertBranch(obj, keys):
    current = obj
    numberOfKeys = len(keys)
    for i in range(numberOfKeys):
        key = keys[i]
        if key not in current:
            if i < numberOfKeys - 1:
                current[key] = {}
            else:
                current[key] = None
        current = current[key]
    return obj


def insertIntoObject(obj, keys, value):
    print "Keys: ", keys
    keys = [unicode(k) for k in keys]
    obj = assertBranch(obj, keys)
    numberOfKeys = len(keys)
    current = obj
    for i in range(numberOfKeys - 1):
        current = current[keys[i]]
    current[keys[numberOfKeys-1]] = value
    return obj


class GeoDashDatabaseConnection(object):

    connection = None
    cursor = None

    def exec_query_multiple(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def exec_query_single(self, sql):
        self.cursor.execute(sql)
        row = self.cursor.fetchone()
        value = None
        try:
            value = row[0]
        except:
            value = None
        return value

    def exec_query_single_aslist(self, sql):
        value = self.exec_query_single(sql)
        return value.split(",") if value else []

    def exec_update(self, sql):
        self.cursor.execute(sql)
        self.connection.commit()  # makes sure updates are actually comitted to database

    def __init__(self):
        self.connection = psycopg2.connect(settings.GEODASH_DB_CONN_STR)
        self.cursor = self.connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.cursor.close()
        del self.cursor
        self.connection.close()
