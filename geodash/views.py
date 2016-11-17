import binascii
import errno
import os
import re
import yaml
import StringIO
import tempfile
import shutil
import zipfile

from urlparse import urlparse
#from csv import DictWriter
from osgeo import ogr, osr

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
from geodash.utils import extract, grep, reduceValue, getRequestParameter, getRequestParameters
from geodash.enumerations import ATTRIBUTE_TYPE_TO_OGR


def parse_path(path):
    basepath, filepath = os.path.split(path)
    filename, ext = os.path.splitext(filepath)
    return (basepath, filename, ext)


class GeoDashDictWriter():

    def __init__(self, output, fields, fallback=""):
        self.output = output
        self.fields = fields
        self.fallback = fallback
        self.delimiter = u","
        self.quote = u'"'
        self.newline = u"\n"

    def _reduce(self, row, feature=None):
        for i in range(len(self.fields)):
            for r in extract('reduce', self.fields[i], []):
                row[i] = reduceValue(r, row[i], feature=feature)
        return row

    def _process_attr(self, attr, obj):
        if 'value' in attr:
            return attr.get('value')
        else:
            return extract(attr.get('path'), obj, self.fallback)

    def writeheader(self):
        self.output = self.output + self.delimiter.join([self.quote+x['label']+self.quote for x in self.fields]) + self.newline

    def writerow(self, rowdict):
        row = [self._process_attr(x, rowdict) for x in self.fields]
        #
        row = self._reduce(row, feature=rowdict)
        row = [unicode(x) for x in row]
        row = [x.replace('"','""') for x in row]
        #
        self.output = self.output + self.delimiter.join([self.quote+x+self.quote for x in row]) + self.newline

    def writerows(self, rowdicts):
        rows = []
        for rowdict in rowdicts:
            row = [self._process_attr(x, rowdict) for x in self.fields]
            #
            row = self._reduce(row, feature=rowdict)
            row = [unicode(x) for x in row]
            row = [x.replace('"','""') for x in row]
            #
            rows.append(row)

        for row in rows:
            self.output = self.output + self.delimiter.join([self.quote+x+self.quote for x in row]) + self.newline

    def getvalue(self):
        return self.output


class geodash_data_view(View):

    key = None

    def _build_root(self, request, *args, **kwargs):
        return None

    def _build_key(self, request, *args, **kwargs):
        return self.key

    def _build_attributes(self, request, *args, **kwargs):
        #raise Exception('geodash_data_view._build_attributes should be overwritten.  This API likely does not support CSV.')
        return None

    def _build_geometry(self, request, *args, **kwargs):
        return None

    def _build_geometry_type(self, request, *args, **kwargs):
        return None

    def _build_grep_post_attributes(self, request, *args, **kwargs):
        return None

    def _build_grep_post_filters(self, request, *args, **kwargs):
        return None

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

        #content = json.dumps(data, default=jdefault)
        #content = re.sub(
        #    settings.GEODASH_REGEX_CLIP_COORDS_PATTERN,
        #    settings.GEODASH_REGEX_CLIP_COORDS_REPL,
        #    content,
        #    flags=re.IGNORECASE)

        root = self._build_root(request, *args, **kwargs)
        attributes = self._build_attributes(request, *args, **kwargs)
        if attributes:
            data = grep(
                obj=data,
                root=root,
                attributes=attributes,
                filters=getRequestParameters(request, "grep", None)
            )

        if ext_lc == "json":
            return HttpResponse(json.dumps(data, default=jdefault), content_type="application/json")
        elif ext_lc == "yml" or ext_lc == "yaml":
            response = yaml.safe_dump(data, encoding="utf-8", allow_unicode=True, default_flow_style=False)
            return HttpResponse(response, content_type="text/plain")
        elif ext_lc == "csv" or ext_lc == "csv":
            writer = GeoDashDictWriter("", attributes)
            writer.writeheader()
            writer.writerows(extract(root, data, []))
            response = writer.getvalue()
            return HttpResponse(response, content_type="text/csv")
        elif ext_lc == "zip":
            # See the following for how to create zipfile in memory, mostly.
            # https://newseasandbeyond.wordpress.com/2014/01/27/creating-in-memory-zip-file-with-python/
            tempDirectory = tempfile.mkdtemp()
            print "Temp Directory:", tempDirectory
            if tempDirectory:
                geometryType = self._build_geometry_type(request, *args, **kwargs)
                ########### Create Files ###########
                os.environ['SHAPE_ENCODING'] = "utf-8"
                # See following for how to create shapefiles using OGR python bindings
                # https://pcjericks.github.io/py-gdalogr-cookbook/vector_layers.html#filter-and-select-input-shapefile-to-new-output-shapefile-like-ogr2ogr-cli
                basepath, out_filename, ext = parse_path(request.path)
                out_shapefile = os.path.join(tempDirectory, out_filename+".shp" )
                out_driver = ogr.GetDriverByName("ESRI Shapefile")
                if os.path.exists(out_shapefile):
                    out_driver.DeleteDataSource(out_shapefile)
                out_datasource = out_driver.CreateDataSource(out_shapefile)
                out_layer = out_datasource.CreateLayer(
                    (out_filename+".shp").encode('utf-8'),
                    geom_type=geometryType
                )
                ########### Create Fields ###########
                out_layer.CreateField(ogr.FieldDefn("id", ogr.OFTInteger))  # Create ID Field
                for attribute in attributes:
                    label = attribute.get('label_shp') or attribute.get('label')
                    out_layer.CreateField(ogr.FieldDefn(
                        label,
                        ATTRIBUTE_TYPE_TO_OGR.get(attribute.get('type', 'string'))
                    ))
                ########### Create Features ###########
                features = extract(root, data, []);
                features_baked = []
                for i in range(len(features)):
                    feature = features[i]
                    feature_baked = {
                        "properties": {},
                        "geometry": extract(self._build_geometry(request, *args, **kwargs), feature, None)
                    }
                    #
                    for attribute in attributes:
                        out_value = attribute.get('value', extract(attribute.get('path'), feature, None))
                        for r in extract('reduce', attribute, []):
                            out_value = reduceValue(r, out_value, feature=feature)
                        feature_baked['properties'][attribute.get('label_shp') or attribute.get('label')] = out_value
                    #
                    features_baked.append(feature_baked)

                grep_post_filters = self._build_grep_post_filters(request, *args, **kwargs)
                if grep_post_filters:
                    features_baked = grep(
                        obj=features_baked,
                        root=None,
                        attributes=self._build_grep_post_attributes(request, *args, **kwargs),
                        filters=grep_post_filters
                    )

                for i in range(len(features_baked)):
                    feature_baked = features_baked[i]
                    outFeature = ogr.Feature(out_layer.GetLayerDefn())
                    outFeature.SetGeometry(ogr.CreateGeometryFromJson(json.dumps(feature_baked['geometry'], default=jdefault)))
                    outFeature.SetField("id", i)
                    for attributeName, attributeValue in feature_baked['properties'].iteritems():
                        outFeature.SetField(
                            attributeName,
                            attributeValue.encode('utf-8') if isinstance(attributeValue, basestring) else attributeValue
                        )
                    out_layer.CreateFeature(outFeature)

                out_datasource.Destroy()
                ########### Create Projection ###########
                spatialRef = osr.SpatialReference()
                spatialRef.ImportFromEPSG(4326)
                spatialRef.MorphToESRI()
                with open(os.path.join(tempDirectory, out_filename+".prj"), 'w') as f:
                    f.write(spatialRef.ExportToWkt())
                    f.close()
                ########### Create Zipfile ###########
                buff = StringIO.StringIO()
                zippedShapefile = zipfile.ZipFile(buff, mode='w')
                #memoryFiles = []
                component_filenames= os.listdir(tempDirectory);
                #for i in range(len(componentFiles)):
                #    memoryFiles.append(StringIO.StringIO())
                for i in range(len(component_filenames)):
                    with open(os.path.join(tempDirectory, component_filenames[i]), 'r') as f:
                        contents = f.read()
                        zippedShapefile.writestr(component_filenames[i], contents)
                zippedShapefile.close()

                print "zippedShapefile.printdir()", zippedShapefile.printdir()

                ########### Delete Temporary Directory ###########
                shutil.rmtree(tempDirectory)
                ########### Response ###########
                return HttpResponse(buff.getvalue(), content_type="application/zip")
                #for i in range(len(componentFiles)):
                #    with open(componentFiles[i], 'w') as componentFile:
                #        memoryFiles[i].write(componentFile.read())
            else:
                raise Http404("Could not acquire temporary directory for building shapefile.")
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
