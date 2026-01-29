from . import usd_updater
from . import usd_check
import importlib


def reload_modules():
    from . import usd_updater
    from . import usd_parser
    from . import usd_check
    from . import assetitem
    importlib.reload(usd_updater)
    importlib.reload(usd_parser)
    importlib.reload(usd_check)
    importlib.reload(assetitem)


def startUpdateAssetsUSD(
        openType,
        tmpfile=None,
        prism_core=None,
        ar_context=None):
    usd_updater.startUpdateAssetsUSD(
        openType=openType,
        tmpfile=tmpfile,
        prism_core=prism_core,
        ar_context=ar_context
    )
    
def checkHoudiniImportsUpdates(): # pragma: no cover
    usd_check.checkEveryNodes()