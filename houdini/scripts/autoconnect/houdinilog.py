print_debug=True
print_info=True
    
def pinfo(toPrint):
    if print_info is True:
        print("Info - " + str(toPrint))
    else:
        pass

def pdebug(toPrint):
    if print_debug is True:
        print("Debug - " + str(toPrint))
    else:
        pass