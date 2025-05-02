from . import sanitycore
import importlib

def main(*args):
    importlib.reload(sanitycore)
    return sanitycore.main(*args)