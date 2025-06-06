PRINT_DEBUG = False
PRINT_INFO = True
    
def pinfo(toPrint):
    if PRINT_INFO is True:
        print("Info - " + str(toPrint))
    else:
        pass

def pdebug(toPrint):
    if PRINT_DEBUG is True:
        print("Debug - " + str(toPrint))
    else:
        pass