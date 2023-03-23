import pymel.core as pm
def run():
    print("STARTUP SCRIPT REMAP")
    dso = pm.ls(type="aiStandIn")
    for d in dso:
        d.dso.set("I:/battlestar_2206/assets/windowsB/publish/ass/windowsB_HD/v005/windowsB_HD.ass")
    print("FOUND !")
    print(dso)
