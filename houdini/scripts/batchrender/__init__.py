
from . import batchrender
import importlib

def main():
    importlib.reload(batchrender)
    batchrender.main()