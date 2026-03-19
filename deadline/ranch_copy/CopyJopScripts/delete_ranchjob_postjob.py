# Script that will be executed after a render job to delete the ranch copy job
# This script is added automatically if render job has access to ranch workers

from Deadline.Scripting import *


def __main__(*args):

    deadlinePlugin = args[0]
    job = deadlinePlugin.GetJob()
    # copy_job_id = job.GetJobExtraInfoKeyValue("copyJobId")
    copy_job_id = job.GetJobExtraInfoKeyValue("copyJobId")
    copy_job = RepositoryUtils.GetJob(copy_job_id, True)
    if not copy_job : 
        print("Job not found : Ending task")
        return
    print(f"Copy job : {copy_job}, id : {copy_job_id}")
    # RepositoryUtils.DeleteJob(copy_job)
    RepositoryUtils.CompleteJob(copy_job)
    print("Artificially completed copy job")