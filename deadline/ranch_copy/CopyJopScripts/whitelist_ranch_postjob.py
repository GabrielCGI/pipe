## Post-Job script for RANCH copy job, whitelists ranch workers from parent render job

from Deadline.Events import *
from Deadline.Scripting import *

def whitelist_ranch_from_job(parent_job_id):
    """ whitelist all ranch machines from given job id

    Args:
        parent_job_id (_type_): _description_
    """

    ranch_workers = []
    
    for name in RepositoryUtils.GetSlaveNames(True):
        if "RANCH" in name:
            ranch_workers.append(name)

    RepositoryUtils.RemoveSlavesFromMachineLimitList(parent_job_id, ranch_workers)
    print(f"Whitelisted ranch machines for job {parent_job_id}")

def __main__(*args):

    deadlinePlugin = args[0]
    job = deadlinePlugin.GetJob()
    parentJob = job.GetJobExtraInfoKeyValue("parentJobId")

    print("Post job script executed")

    whitelist_ranch_from_job(parentJob)
