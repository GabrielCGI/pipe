import sys


def inject_external_libs():
    if not sys.version_info[0] == 3:
        sys.exit(1)

    LIBRARIES_PATH = ( 
        "R:/pipeline/networkInstall/python_shares/"
        f"python3{sys.version_info[1]}_nuke_magnific_pkgs/Lib/site-packages"
    )
    if not LIBRARIES_PATH in sys.path:
        sys.path.insert(0, LIBRARIES_PATH)