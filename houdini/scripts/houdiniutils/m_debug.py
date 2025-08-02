import sys

DEBUG_MODE = True
try:
    sys.path.append(r'R:\devmaxime\virtualvens\sanitycheck\Lib\site-packages')
    import debugpy
except:
    DEBUG_MODE = False


def debug(version="20.5.591"):
    if not DEBUG_MODE:
        return
    
    hython = (
        "C:/Program Files/Side Effects Software"
        f"/Houdini {version}/bin/hython3.11.exe"
    )
    debugpy.configure(python=hython)
    try:
        debugpy.listen(5678)
    except Exception as e:
        print(e)
        return
    
    print("Waiting for debugger attach")
    debugpy.wait_for_client()