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
                obj = extract(newKeyChain, node[""+keyChain[0]], fallback)
    else:
        obj = fallback

    return obj

def grep(obj, root, filters):
    if filters is None:
        return obj
    else:
        if root is None:
            for f in filters:
                filtered = []
                for item in obj:
                    if extract(f['path'], item, None) == f['value']:
                        filtered.append(item)
                obj = filtered
        else:
            for f in filters:
                items = extract(root, obj, None)
                if items is not None:
                    filtered = []
                    for item in items:
                        if extract(f['path'], item, None) == f['value']:
                            filtered.append(item)
                    obj[root] = filtered

        return obj
