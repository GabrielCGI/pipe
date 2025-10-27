from . import cleanexternalreads
import importlib

def main(debug_mode=False, silent_mode=False):
    importlib.reload(cleanexternalreads)
    cleanexternalreads.main(debug_mode, silent_mode)