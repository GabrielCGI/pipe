from Deadline.Events import *
from Deadline.Scripting import *
import os
import re
import sys
import subprocess

def GetDeadlineEventListener():
    """This is the function that Deadline calls to get an instance of the
    main DeadlineEventListener class.
    """
    return ExrToMov()

def CleanupDeadlineEventListener(deadlinePlugin):
    """This is the function that Deadline calls when the event plugin is
    no longer in use so that it can get cleaned up.
    """
    deadlinePlugin.Cleanup()

class ExrToMov(DeadlineEventListener):
    """This is the main DeadlineEventListener class for MyEvent"""
    def __init__(self):
        # Set up the event callbacks here
        self.OnJobFinishedCallback += self.OnJobFinished

    def Cleanup(self):
        del self.OnJobFinishedCallback

    def OnJobFinished(self, job):
        """On Job finished create a mov file
        """
        # Cancel if the comment -no-exr-to-mov
        match = re.match(r"^.*--no-exr-to-mov.*$",job.JobComment)
        if match:
            print("No EXR to MOV")
            return

        # Retrieve datas from the job
        output_directory = job.OutputDirectories[0]
        first_frame = min(job.Frames)
        last_frame = max(job.Frames)
        frame_range = str(first_frame)+"-"+str(last_frame)
        print("Output directory: " +str(output_directory))

        # Compute input files path and output file path
        input_file = os.path.join(output_directory, job.OutputFileNames[0])
        input_file = re.sub( "\?", "#", input_file )
        first_frame_file = FrameUtils.ReplacePaddingWithFrameNumber(input_file, first_frame)
        trim = first_frame_file[:-9]
        input_file= (trim + ".####.exr").replace("\\", "/")
        output_file =  (trim + "_preview").replace("\\", "/")
        if len(job.Frames)>2:
            output_file+=".mov"
        else:
            output_file+=".jpg"
        print("Input files: " +input_file)
        print("Output file: " +output_file)
        print("Frame range: " +frame_range)

        # Launch exr2mov
        bat_file_path = r'R:\pipeline\pipe\nuke\exr2mov\data\exr2mov_deadline.bat'
        subprocess.run([bat_file_path, input_file, output_file, frame_range])

        job.JobExtraInfo0 = output_file
