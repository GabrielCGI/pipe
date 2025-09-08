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


def startUpdateAssetsUSD(openType, tmpfile=None, ar_context=None):
    usd_updater.startUpdateAssetsUSD(
        openType=openType,
        tmpfile=tmpfile,
        ar_context=None
    )
    
def checkHoudiniImportsUpdates():
    usd_check.checkEveryNodes()