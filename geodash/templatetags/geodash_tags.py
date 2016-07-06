import bleach
import markdown
import re

try:
    import simplejson as json
except ImportError:
    import json

from django import template
from django.template.loader import get_template

register = template.Library()


@register.filter(name='tabLabel')
def tabLabel(value):
    if len(value.split(' ')) == 2:
        return value.replace(' ', '<br>')
    else:
        return value

@register.filter(name='isVisible')
def isVisible(value):
    return value.get('visible', True)


@register.filter(name='formatLabel')
def formatLabel(value, arg):
    return value.format(value=arg)


@register.filter(name='as_json')
def as_json(value):
    return json.dumps(value)


@register.filter(name='md2html')
def md2html(value):
    md = markdown.markdown(value).strip()[len("<p>"):-1*len("</p>")]
    md = bleach.clean(md)
    md = re.sub(r"(<a .*)>(.*?)</a>", r'\1 target="_blank">\2</a>', md, flags=(re.M | re.I))
    return md


@register.filter(name="template2string")
def template2string(value):
    t = get_template(value)
    text = t.render({})
    text = text.replace("\r\n", "").replace("\n", "").replace("\"", "\\\"")
    return text


@register.filter(name="sortItemsByList")
def sortItemsByList(value, arg):
    if value and arg:
        layers = [layer for layer in value if layer[0] in arg]
        s = sorted(layers, key=lambda x: arg.index(x[0]))
        return s
    else:
        return value

@register.filter(name="sortItemsBySchema")
def sortItemsBySchema(value, arg):
    if value and arg:
        return sorted(value, key=lambda x: arg[x[0]].get('order', 0))
    else:
        return value


@register.filter(name="sortListByList")
def sortListByList(value, arg):
    if arg:
        s = sorted(value, key=lambda x: arg.index(x["id"]))
        return s
    else:
        return value


@register.filter(name="legendGraphic")
def legendGraphic(value, arg=None):
    layer = value
    symbol = layer["cartography"][0]["legend"]["symbol"]
    if symbol.get("url", None):
        return layer["legend"]["symbol"]["url"]
    else:
        params = {
            "REQUEST": "GetLegendGraphic",
            "VERSION": layer["wms"]["version"] or "1.1.1",
            "FORMAT": layer["wms"]["format"] or "image/png",
            "WIDTH": symbol["width"] or 20,
            "HEIGHT": symbol["height"] or 20,
            "LAYER": layer["wms"]["layers"][arg] if arg and arg >= 0 else layer["wms"]["layers"][0]
        }
        if layer["wms"]["styles"] and arg >= 0:
            params["STYLE"] = layer["wms"]["styles"][arg]
        qs = "&".join(['%s=%s' % (k, v) for (k, v) in params.items()])
        url = layer["wms"]["url"]+"?"+qs
        print url
        return url


@register.filter(name="as_float")
def as_float(value):
    return value * 1.0


@register.filter(name="addFloat")
def addFloat(value, arg):
    return value + arg


@register.filter(name="subtract")
def subtract(value, arg):
    return value - arg


@register.filter(name="divide")
def divide(value, arg):
    return value / arg


@register.filter(name="percent")
def percent(value, arg):
    return 100.0 * value / arg

@register.filter(name="lookup")
def lookup(d, key):
    return d[key]

@register.filter(name="geodash_field_id")
def geodash_field_id(value):
    return value.lower().replace(".","-").replace(" ","-")
