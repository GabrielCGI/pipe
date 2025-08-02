from . import usd_updater
import importlib


def startUpdateAssetsUSD(openType, tmpfile=None, ar_context=None):
    importlib.reload(usd_updater)
    usd_updater.startUpdateAssetsUSD(
        openType=openType,
        tmpfile=tmpfile,
        ar_context=None
    )