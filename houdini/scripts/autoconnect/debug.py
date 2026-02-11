import sys

DEBUG_MODE = True
try:
    sys.path.append(r'R:\devmaxime\virtualvens\sanitycheck\Lib\site-packages')
    import debugpy
except:
    DEBUG_MODE = False


def debug():
    if not DEBUG_MODE:
        return
    
    hython = r"C:\Program Files\Side Effects Software\Houdini 20.5.591\bin\hython3.11.exe"
    debugpy.configure(python=hython)
    try:
        debugpy.listen(5678)
    except Exception as e:
        print(e)
        return
    
    print("Waiting for debugger attach")
    debugpy.wait_for_client()