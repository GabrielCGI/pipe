## Pre-job script for render jobs with RANCH workers. 
## Creates a job that will allow RANCH computers to compute and copy all dependencies

# region Imports

#Deadline
from Deadline.Events import *
from Deadline.Scripting import *

# Handle json files
import json

# System and path handlers
import os
from pathlib import Path

# log
import logging 
import datetime

import time

# endregion

# region Global variables 

RANCH_GROUPS = ["husk_grp" , "ranch_grp" , "debugranch"]
RANCH_ONLY = "debugranch"
USD_EXT = [".usdc" , ".usda"]
PYTHON_JOB_SCRIPT = r"R:\pipeline\pipe\deadline\ranch_copy\CopyJopScripts\ranch_copy_job.py"
PYTHON_JOB_POSTJOB_SCRIPT = r"R:\pipeline\pipe\deadline\ranch_copy\CopyJopScripts\whitelist_ranch_postjob.py"
RANCH_CPY_LOG_DIR = "C:/RANCH_CPY_log/"
# endregion

# region Helper functions

def setup_logs():
    os.makedirs(RANCH_CPY_LOG_DIR, exist_ok=True)
    log_filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_copy_exr.log")
    log_path = os.path.join(RANCH_CPY_LOG_DIR, log_filename)

    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def log_info(msg):
    logging.info(msg)
    print(msg)

def log_warning(msg):
    logging.warning
    print(msg)

def log_error(msg):
    logging.error(msg)
    print(msg)

def findUSDPath(deadlinePlugin):
    """
    Input : Deadline plugin 
    Output : Path to the export usd file (Pathlib path type) 
    """
    job = deadlinePlugin.GetJob()
    dir = Path(job.JobOutputDirectories[0]) / "_usd"
    exr = job.JobOutputFileNames[0]

    # Handle case where the usd doesnt work
    if not os.path.isdir(dir):
        log_error(f"USD directory not found {dir}")

        return None

    for file in os.scandir(dir):
        filename = file.name
        for ext in USD_EXT :
            if filename.endswith(ext):
                log_info(f"USD found at : {filename}")
                return Path(file)

    log_error(f"USD file not found in folder : {dir}")
    return None



def blacklist_ranch(deadlinePlugin):
    """blacklist all ranch workers from current job

    Args:
        deadlinePlugin (Deadline plugin): deadline plugin that contains job info
    """
    job = deadlinePlugin.GetJob()
    jobId = job.JobId
    slave_name = deadlinePlugin.GetSlaveName() # Store our name to not be blacklisted

    # 
    ranch_workers = []

    for name in RepositoryUtils.GetSlaveNames(True) :
        if "RANCH" in name:
            ranch_workers.append(name)

    RepositoryUtils.AddSlavesToMachineLimitList(jobId, ranch_workers)
    log_info(f"Blacklisted ranch workers : {ranch_workers}")

def submit_deadline_job(deadlinePlugin, usd_path):
    """create and submit a deadline job that will handle computing and copying dependencies to ranch

    Args:
        deadlinePlugin (_type_): deadline info 
        usd_path (Path): full path to usd file

    Returns:
        string: created job id
    """

    parent_job = deadlinePlugin.GetJob()

    jobInfo = {
        "Name": f"{parent_job.JobName}_ranch_copy", # Add ranch copy to current job name
        "Plugin": "Python",             
        "Group": RANCH_ONLY,                        # Defined above, the group with only ranch workers (debugranch for now)
        # "Pool": "urgent",                           # Urgent for ranch scripts to quickly get onto this
        "SecondaryPool": "none",
        "Priority": "50",
        "Frames": "1",
        "ChunkSize": "1",
        "MachineLimit": "0",
        "Comment": "Ranch-Dependency-Copy-Job",
        "BatchName": parent_job.BatchName or parent_job.JobName,
        "UserName" : parent_job.JobUserName,
        "PostJobScript" : PYTHON_JOB_POSTJOB_SCRIPT,
        "ExtraInfoKeyValue0" : f"parentJobId={parent_job.JobId}",          # Transfer this job id to the created job to allow whitelisting
    }

    pluginInfo = {
        "Version": "3.11",
        "ScriptFile": PYTHON_JOB_SCRIPT,
        "Arguments": f"--usd \"{usd_path}\"", 
    }
    
    # homeDir = r'C:\tmp\deadline_job'
    homeDir = ClientUtils.GetCurrentUserHomeDirectory()

    jobInfoFile = os.path.join(homeDir, "temp" , "python_job_info.job")
    pluginInfoFile = os.path.join(homeDir, "temp" , "python_plugin_info.job")

    arguments = []
    arguments.append(jobInfoFile)
    arguments.append(pluginInfoFile)

    with open(arguments[0], "w") as fileHandle:
        for i in jobInfo:
            fileHandle.write("%s=%s\n" % (i, jobInfo[i]))

    with open(arguments[1], "w") as fileHandle:
        for i in pluginInfo:
            fileHandle.write("%s=%s\n" % (i, pluginInfo[i]))

    new_job_id = RepositoryUtils.SubmitJob(arguments)
    log_info(f"Submitted RanchCopy job: {new_job_id}")

    return new_job_id

# endregion

# region Main

# Test main to check if the deadlinePlugin is properly found. 
def __main__(*args):

    deadlinePlugin = args[0]
    job = deadlinePlugin.GetJob()
    setup_logs()

    log_info("Launched prejob script")

    # If ranch pool not in the pools, return
    if not job.JobGroup in RANCH_GROUPS :
        log_info("Ranch workers not in this job")
        return 
    
    # Blacklist all ranch from this job
    blacklist_ranch(deadlinePlugin)

    usd_path = findUSDPath(deadlinePlugin)

    if not usd_path :
        log_info(f"Blacklisted ranch, and not creating copy job") 
        return

    copy_job = submit_deadline_job(deadlinePlugin , usd_path)
    # job.SetJobExtraInfoKeyValue("copyJobId" , copy_job.JobId)
    job.SetJobExtraInfoKeyValue("copyJobId", copy_job.JobId)
    RepositoryUtils.SaveJob(job)

# endregion