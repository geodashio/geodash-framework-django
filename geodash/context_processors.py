from django.conf import settings

from geodash.enumerations import MONTHS_NUM, MONTHS_LONG, MONTHS_SHORT3, MONTHS_ALL, DAYSOFTHEWEEK

def geodash(request):
    """Global values to pass to templates"""

    ctx = {
        "MONTHS_NUM": MONTHS_NUM,
        "MONTHS_SHORT3": MONTHS_SHORT3,
        "MONTHS_LONG": MONTHS_LONG,
        "MONTHS_ALL": MONTHS_ALL,
        "DAYSOFTHEWEEK": DAYSOFTHEWEEK,
        "GEODASH_STATIC_VERSION": settings.GEODASH_STATIC_VERSION,
        "GEODASH_STATIC_DEBUG": settings.GEODASH_STATIC_DEBUG,
        "GEODASH_STATIC_DEPS": settings.GEODASH_STATIC_DEPS,
        "GEODASH_DNS_PREFETCH": settings.GEODASH_DNS_PREFETCH
    }

    return ctx
