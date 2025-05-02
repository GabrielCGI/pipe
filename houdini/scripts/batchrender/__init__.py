
from . import batchrender, test
import importlib

def main():
    importlib.reload(batchrender)
    batchrender.main()
    
def debug():
    importlib.reload(test)
    test.main()