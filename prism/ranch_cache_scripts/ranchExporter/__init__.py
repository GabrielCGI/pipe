from . import ranchExporter
import importlib

def parseAndCopyToRanch(usdpath, kwargs):
    importlib.reload(ranchExporter)
    ranchExporter.parseAndCopyToRanch(usdpath, kwargs)

def is_light_cache(kwargs):
    return ranchExporter.is_light_cache(kwargs)

def getUsdPath(kwargs):
    return ranchExporter.getUsdPath(kwargs)

def parseAndCopyToRanchDev(usdpath, kwargs):
    print('RanchExport parseAndCopy Dev Mode')
    from . import ranchExporter_dev
    importlib.reload(ranchExporter_dev)
    ranchExporter_dev.parseAndCopyToRanch(usdpath, kwargs)