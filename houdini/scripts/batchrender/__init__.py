
from . import batchrender
from . import farmsubmitter
import importlib


def main():
    importlib.reload(batchrender)
    importlib.reload(farmsubmitter)
    batchrender.main()
    

