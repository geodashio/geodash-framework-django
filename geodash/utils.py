import re

def extract(keyChain, node, fallback):

    if isinstance(keyChain, basestring):
        keyChain = keyChain.split(".");

    obj = None

    if node is not None:
        if len(keyChain) == 0:
            obj = node
        else:
            newKeyChain = keyChain[1:]
            if len(newKeyChain) == 0:
                if isinstance(keyChain[0], basestring) and keyChain[0].lower() == "length":
                    if isinstance(node, list):
                        obj = len(node)
                    else:
                        obj = node.get("length", 0)

        if (obj is None) and (node is not None):
            if isinstance(node, list):
                index = int(keyChain[0]) if isinstance(keyChain[0], basestring) else keyChain[0]
                obj = extract(newKeyChain, node[index], fallback)
            else:
                obj = extract(newKeyChain, node.get(""+keyChain[0]), fallback)
    else:
        obj = fallback

    return obj

def getRequestParameters(request, name, fallback):
    value = None
    params = request.GET.lists()
    if params:
        for k, v in params:
            if k == name:
                value = v
                break

    if value == None:
        value = fallback
    return value

def testValue(obj=None, path=None, operand=None, valueType=None, value_test=None, value_min=None, value_max=None):

    if operand == "=" or operand == u"=":
        if valueType == "int" or valueType == "integer" or valueType == u"int" or valueType == u"integer":
            return extract(path, obj, None) == int(value_test)
        elif valueType == "double" or valueType == "float" or valueType == u"double" or valueType == u"float":
            return extract(path, obj, None) == float(value_test)
        else:
            return extract(path, obj, None) == value_test
    elif operand == "between" or operand == "btwn":
        if valueType == "int" or valueType == "integer" or valueType == u"int" or valueType == u"integer":
            try:
                value = extract(path, obj, None)
                return value >= int(value_min) and value <= int(value_max)
            except:
                return False
        elif valueType == "double" or valueType == "float" or valueType == u"double" or valueType == u"float":
            try:
                value = extract(path, obj, None)
                return value >= float(value_min) and value <= float(value_max)
            except:
                return False
        else:
            return False
    else:
        return True

def parseFilter(x):
    m = re.match("^([A-Za-z0-9_.]+)(\\s*)([=><])(\\s*)(.+)$", x, re.MULTILINE|re.IGNORECASE)
    if m:
        return {'path': m.group(1), 'operand': m.group(3), 'value': m.group(5)}
    else:
        m = re.match("^([A-Za-z0-9_.]+)(\\s*)(between|btwn)(\\s*)([0-9.]+)(\\s*)(and)(\\s*)([0-9.]+)$", x, re.MULTILINE|re.IGNORECASE)
        if m:
            return {'path': m.group(1), 'operand': m.group(3), 'min': m.group(5), 'max': m.group(9)}
        else:
            return None

def grep(**kwargs):

    obj = kwargs.get('obj')
    root = kwargs.get('root')
    attributes = kwargs.get('attributes')
    filters = kwargs.get('filters')

    attribute_map = {}
    for path in [x['path'] for x in attributes if x.get('type') == "integer" or x.get('type') == "int"]:
        attribute_map[path] = "int"
    for path in [x['path'] for x in attributes if x.get('type') == "double" or x.get('type') == "float"]:
        attribute_map[path] = "float"

    if filters is None:
        return obj
    else:
        if root is None:
            for f in filters:
                filtered = []
                if isinstance(f, basestring):
                    f2 = parseFilter(f)
                    if f2:
                        for item in obj:
                            include = testValue(
                                obj=item,
                                path=f2['path'],
                                value_test=f2.get('value'),
                                value_min=f2.get('min'),
                                value_max=f2.get('max'),
                                operand=f2['operand'],
                                valueType=attribute_map.get(f2["path"], "string"))
                            if include:
                                filtered.append(item)

                else:
                    for item in obj:
                        if extract(f['path'], item, None) == f['value']:
                            filtered.append(item)
                obj = filtered
        else:
            for f in filters:
                items = extract(root, obj, None)
                if items is not None:
                    filtered = []
                    if isinstance(f, basestring):
                        f2 = parseFilter(f)
                        if f2:
                            for item in items:
                                include = testValue(
                                    obj=item,
                                    path=f2['path'],
                                    value_test=f2.get('value'),
                                    value_min=f2.get('min'),
                                    value_max=f2.get('max'),
                                    operand=f2['operand'],
                                    valueType=attribute_map.get(f2["path"], "string"))
                                if include:
                                    filtered.append(item)
                    else:
                        for item in items:
                            if extract(f['path'], item, None) == f['value']:
                                filtered.append(item)

                    obj[root] = filtered

        return obj
