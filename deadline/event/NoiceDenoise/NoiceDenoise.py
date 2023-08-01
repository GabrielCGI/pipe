from Deadline.Events import *
from Deadline.Scripting import *
import os
import re
import sys
sys.path.append("R:/pipeline/pipe/maya/scripts/deadline")
import read_exr_metadata
from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

################################################################################

FIELDS = {
    "po" : "none",                  # Pool
    "sp" : "",                      # Secodnary Pool
    "g" : "none",                   # Group
    "prio" : 99,                    # Priority
    "tt" : 0,                       # Task Timeout
    "att" : False,                  # Auto Task Timeout
    "ct" : 1,                       # Concurrent Tasks
    "lct" : True,                   # Limit Concurrent Tasks
    "mlim" : 0,                     # Machine Limit
    "mbl" : False,                  # Machine Blacklist
    "mlis" : "",                    # Machine List
    "l" : "",                       # Limits
    "d" : "",                       # Dependencies
    "ojc" : "Nothing",              # On Job Complete
    "sas" : False,                  # Submit Job As Suspended
    "fpt" : 1,                      # Frames per Task
    "ef" : 1,                       # Extra Frames
    "pr" : 1,                       # Patch Radius
    "sr" : 9,                       # Search Radius
    "v" : 0.5                       # Variance

    # Additionnal not overridable fields

    # un                            + User Name
    # jn                            + Job Name
    # c                             + Comment
    # d                             + Department
    # ip                            + Input Pattern
    # op                            + Output Pattern
    # fl                            + Frames List
    # aovs                          + AOVs
}

################################################################################

def GetDeadlineEventListener():
    """
    This is the function that Deadline calls to get an instance of the
    main DeadlineEventListener class.
    """
    return NoiceDenoise()

def CleanupDeadlineEventListener(deadlinePlugin):
    """
    This is the function that Deadline calls when the event plugin is
    no longer in use so that it can get cleaned up.
    """
    deadlinePlugin.Cleanup()

class NoiceDenoise(DeadlineEventListener):
    """
    This is the main DeadlineEventListener class for MyEvent
    """
    def __init__(self):
        # Set up the event callbacks here
        self.OnJobFinishedCallback += self.OnJobFinished
        # Datas for the job cration
        self.__fields_datas = FIELDS.copy()

    def Cleanup(self):
        del self.OnJobFinishedCallback

    def __retrieve_fields_datas(self, job, override_str, comment):
        output_directory = job.OutputDirectories[0]
        input_file = re.sub( "\?", "#",os.path.join(output_directory,job.OutputFileNames[0]))
        first_frame = min(job.Frames)
        last_frame = max(job.Frames)

        # Get overrided datas
        if override_str is not None:
            override_dict = {}
            override_pairs = override_str.split(',')
            for pair in override_pairs:
                exec(pair.strip(), None, override_dict)
            for key, value in override_dict.items():
                if key in self.__fields_datas:
                    self.__fields_datas[key]=value

        # Get not overridable datas
        input_pattern = FrameUtils.ReplacePaddingWithFrameNumber(input_file, first_frame)
        dirname_input_pattern, filename_input_pattern = os.path.split(input_pattern)
        self.__fields_datas["un"] = job.JobUserName
        self.__fields_datas["jn"] = job.JobName + "_denoise_job"
        self.__fields_datas["c"] = comment
        self.__fields_datas["d"] = job.JobDepartment
        self.__fields_datas["ip"] = input_pattern
        self.__fields_datas["op"] = os.path.join(dirname_input_pattern,"denoised",filename_input_pattern)
        self.__fields_datas["fl"] = str(first_frame)+"-"+str(last_frame)
        try:
            self.__fields_datas["aovs"] = " ".join(read_exr_metadata.parse_aov_list(input_pattern))
        except:
            print("Error while parsing EXR")
            return False
        return True

    def __submit_denoise_job(self):
        """
        Launch a job to denoise the sequence by using the data retrieved
        """

        # Job Options
        job_file = os.path.join(ClientUtils.GetDeadlineTempPath(), "noice_job_info.job")
        writer_job = StreamWriter(job_file, False, Encoding.Unicode)
        writer_job.WriteLine("Plugin=Noice")
        writer_job.WriteLine("UserName={0}".format(self.__fields_datas["un"]))
        writer_job.WriteLine("Name={0}".format(self.__fields_datas["jn"]))
        writer_job.WriteLine("Comment={0}".format(self.__fields_datas["c"]))
        writer_job.WriteLine("Department={0}".format(self.__fields_datas["d"]))
        writer_job.WriteLine("Pool={0}".format(self.__fields_datas["po"]))
        writer_job.WriteLine("SecondaryPool={0}".format(self.__fields_datas["sp"]))
        writer_job.WriteLine("Group={0}".format(self.__fields_datas["g"]))
        writer_job.WriteLine("Priority={0}".format(self.__fields_datas["prio"]))
        writer_job.WriteLine("TaskTimeoutMinutes={0}".format(self.__fields_datas["tt"]))
        writer_job.WriteLine("EnableAutoTimeout={0}".format(self.__fields_datas["att"]))
        writer_job.WriteLine("ConcurrentTasks={0}".format(self.__fields_datas["ct"]))
        writer_job.WriteLine("LimitConcurrentTasksToNumberOfCpus={0}".format(self.__fields_datas["lct"]))
        writer_job.WriteLine("MachineLimit={0}".format(self.__fields_datas["mlim"]))
        if self.__fields_datas["mbl"]:
            writer_job.WriteLine("Blacklist={0}".format(self.__fields_datas["mlis"]))
        else:
            writer_job.WriteLine("Whitelist={0}".format(self.__fields_datas["mlis"]))
        writer_job.WriteLine("LimitGroups={0}".format(self.__fields_datas["l"]))
        writer_job.WriteLine("JobDependencies={0}".format(self.__fields_datas["d"]))
        writer_job.WriteLine("OnJobComplete={0}".format(self.__fields_datas["ojc"]))
        if(self.__fields_datas["sas"]): writer_job.WriteLine("InitialStatus=Suspended")
        writer_job.WriteLine("OutputFilename0={0}".format(self.__fields_datas["op"]))
        writer_job.WriteLine("OutputDirectory0={0}".format(
            os.path.join(os.path.dirname(self.__fields_datas["ip"]),"denoised")))
        writer_job.WriteLine("Frames={0}".format(self.__fields_datas["fl"]))
        writer_job.WriteLine("ChunkSize={0}".format(self.__fields_datas["fpt"]))
        writer_job.Close()

        # Plugin options
        plugin_file = os.path.join(ClientUtils.GetDeadlineTempPath(), "noice_plugin_info.job")
        writer_plugin = StreamWriter(plugin_file, False, Encoding.Unicode)
        writer_plugin.WriteLine("InputPattern={0}".format(self.__fields_datas["ip"]))
        writer_plugin.WriteLine("OutputPattern={0}".format(self.__fields_datas["op"]))
        writer_plugin.WriteLine("ExtraFrames={0}".format(self.__fields_datas["ef"]))
        writer_plugin.WriteLine("PatchRadius={0}".format(self.__fields_datas["pr"]))
        writer_plugin.WriteLine("SearchRadius={0}".format(self.__fields_datas["sr"]))
        writer_plugin.WriteLine("Variance={0}".format(self.__fields_datas["v"]))
        writer_plugin.WriteLine("AOV={0}".format(self.__fields_datas["aovs"]))
        writer_plugin.Close()

        # Arguments to create the denoise job
        arguments = StringCollection()
        arguments.Add(job_file)
        arguments.Add(plugin_file)
        result = ClientUtils.ExecuteCommandAndGetOutput(arguments)
        print(result)


    def OnJobFinished(self, job):
        """
        On Job finished launch Noice
        """
        match = re.match(r"^(.*)--denoise(?:\[(.*)\])?(.*)$",job.JobComment)
        if not match:
            print("No denoising. To create automatically a Noice denoise job add --denoise to the comment of your job. \nYou can override parameters by enclosing them in brackets. ex: --denoise[priority:100,patch_radius:3]")
            return

        # Get the override dict as str and keep the remaining comments
        override_str = match.group(2)
        comment = str(match.group(1))+str(match.group(3))
        if not self.__retrieve_fields_datas(job, override_str, comment):
            return
        self.__submit_denoise_job()
