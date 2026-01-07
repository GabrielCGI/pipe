from . import ranchExporter
from . import prism_lop_utils

import importlib


def parseAndCopyToRanch(usdpath, kwargs):
    # return
    importlib.reload(ranchExporter)
    ranchExporter.parseAndCopyToRanch(usdpath, kwargs)

def is_light_cache(kwargs):
    return prism_lop_utils.is_light_cache(kwargs)

def getUsdPath(kwargs):
    return prism_lop_utils.getUsdPath(kwargs)

def parseAndCopyToRanchDev(usdpath, kwargs):
    return
    from . import ranchExporter_dev
    importlib.reload(ranchExporter_dev)
    ranchExporter_dev.parseAndCopyToRanch(usdpath, kwargs)

def parseAndCopyLop(usdpath, kwargs):
    return
    from . import ranchExporterLop
    importlib.reload(ranchExporterLop)
    ranchExporterLop.parseAndCopyToRanch(usdpath, kwargs)