from . import nukelicenseparser
import importlib

def main():
    importlib.reload(nukelicenseparser)
    return nukelicenseparser.main()

if __name__ == '__main__':
    main()