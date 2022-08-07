#!/usr/bin/env python3
from System import *
from System.IO import *
import os




def __main__(deadlinePlugin):
    job = deadlinePlugin.GetJob()
    my_comment = job.Comment
    deadlinePlugin.LogInfo("Setting up env variable for Illogic path mapping. ")
    DISK_I_on_ranch = "//RANCH-159/guerlain_cache/I"
    DISK_R_on_ranch = "//RANCH-159/guerlain_cache/R"

    DISK_I_on_local = "I:"
    DISK_R_on_local = "R:"

    #APPLY ENV VARRIABLE FOR PATH MAMMINF IF IT's A RANCH AND IF THE COMMENT = RANCH_PATH_MAPPING
    if os.environ['COMPUTERNAME'].startswith('RANCH') and  my_comment == "ranch_path_mapping":
        deadlinePlugin.SetProcessEnvironmentVariable("DISK_I", DISK_I_on_ranch)
        deadlinePlugin.SetProcessEnvironmentVariable("DISK_R", DISK_R_on_ranch )
        deadlinePlugin.LogInfo("Setting DISK_I="+DISK_I_on_ranch)
        deadlinePlugin.LogInfo("Setting DISK_R="+DISK_R_on_ranch)
    else:
        deadlinePlugin.SetProcessEnvironmentVariable("DISK_I",DISK_I_on_local)
        deadlinePlugin.SetProcessEnvironmentVariable("DISK_R", DISK_R_on_local)
        deadlinePlugin.LogInfo("Setting DISK_I="+DISK_I_on_local)
        deadlinePlugin.LogInfo("Setting DISK_R="+DISK_R_on_local)
