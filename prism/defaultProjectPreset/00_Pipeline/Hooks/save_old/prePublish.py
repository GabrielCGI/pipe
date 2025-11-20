import os
import time
import sys

SANITYCHECK_PATH = "R:/pipeline/pipe_public/sanitycheck"
ENABLE_SANITY_CHECK = True
sys.path.insert(0, SANITYCHECK_PATH)
try:
    import sanitycheck
except:
    ENABLE_SANITY_CHECK = False

try:
    YAML_LOCATION = os.environ['SANITY_CHECK_CONFIG']
except:
    YAML_LOCATION = "None"
    
def main(*args):
    if ENABLE_SANITY_CHECK:
        args = (*args, YAML_LOCATION)
        res = sanitycheck.main(*args)
        if not res:
            print('Cancel publish')
            return {"cancel": True}
        else:
            sm = args[0]
            msg = 'Sanity check sucessfully passed.'
            popup = sm.core.waitPopup(sm.core, msg)
            with popup:
                time.sleep(0.5)
    
    