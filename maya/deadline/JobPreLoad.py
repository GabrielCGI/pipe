#!/usr/bin/env python3
from System import *
from System.IO import *
import os




def __main__(deadlinePlugin):
    job = deadlinePlugin.GetJob()
    deadlinePlugin.LogInfo("Setting up env variable for Illogic path mapping. ")
    DISK_I_on_ranch = "//RANCH-159/guerlain_cache/I"
    DISK_R_on_ranch = "//RANCH-159/guerlain_cache/R"

    DISK_I_on_local = "I:"
    DISK_R_on_local = "R:"

    if os.environ['COMPUTERNAME'].startswith('RANCH'):
        deadlinePlugin.SetProcessEnvironmentVariable("DISK_I", DISK_I_on_ranch)
        deadlinePlugin.SetProcessEnvironmentVariable("DISK_R", DISK_R_on_ranch )
        deadlinePlugin.LogInfo("Setting DISK_I="+DISK_I_on_ranch)
        deadlinePlugin.LogInfo("Setting DISK_R="+DISK_R_on_ranch)
    else:
        deadlinePlugin.SetProcessEnvironmentVariable("DISK_I",DISK_I_on_local)
        deadlinePlugin.SetProcessEnvironmentVariable("DISK_R", DISK_R_on_local)
        deadlinePlugin.LogInfo("Setting DISK_I="+DISK_I_on_local)
        deadlinePlugin.LogInfo("Setting DISK_R="+DISK_R_on_local)
