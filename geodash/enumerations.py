from osgeo import ogr

MONTHS_NUM = range(0, 12)
MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]  # noqa
MONTHS_SHORT3 = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]  # noqa
MONTHS_ALL = [{'num': i+1, 'long': MONTHS_LONG[i], 'short3': MONTHS_SHORT3[i]} for i in MONTHS_NUM]  # noqa

DAYSOFTHEWEEK = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']  # noqa

ATTRIBUTE_TYPE_TO_OGR = {
    "int": ogr.OFTInteger,
    "integer": ogr.OFTInteger,
    "double": ogr.OFTReal,
    "float": ogr.OFTReal,
    "string": ogr.OFTString
}

GEOMETRY_TYPE_TO_OGR = {
    "point": ogr.wkbPoint,
    "multipolygon": ogr.wkbMultiPolygon
}
