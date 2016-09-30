import numpy


# http://stackoverflow.com/questions/16022556/has-python-3-2-to-bytes-been-back-ported-to-python-2-7
def to_bytes(n, length, endianess='big'):
    h = '%x' % n
    s = ('0'*(len(h) % 2) + h).zfill(length*2).decode('hex')
    return s if endianess == 'big' else s[::-1]


def writeToByteArray(arr, x, i):
    if isinstance(x, list):
        for y in x:
            if isinstance(y, int):
                arr, i = writeIntToByteArray(arr, y, i)
            elif isinstance(y, float):
                arr, i = writeIntToByteArray(arr, int(y), i)
            elif isinstance(y, long):
                arr, i = writeIntToByteArray(arr, int(y), i)
    elif isinstance(x, int):
        arr, i = writeIntToByteArray(arr, x, i)
    elif isinstance(x, float):
        arr, i = writeIntToByteArray(arr, int(x), i)
    elif isinstance(x, long):
        arr, i = writeIntToByteArray(arr, int(x), i)
    else:
        print "Saving a string I thinks", type (x)
        b = bytes(x)
        for z in b:
            arr[i] = z
            i += 1
    return arr, i


def writeIntToByteArray(arr, x, i):
    b = [t for t in to_bytes(x, 4, endianess='big')]
    padding = [t for t in numpy.zeros(4 - len(b), dtype=int)]
    b = padding + b if isinstance(b, list) else padding + [b]
    for z in b:
        arr[i] = z
        i += 1
    return arr, i
