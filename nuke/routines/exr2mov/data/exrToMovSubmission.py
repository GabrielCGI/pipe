from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog
from Deadline.Scripting import *
import os
import re
import sys

import os
import subprocess

sys.path.append("R:/pipeline/pipe/maya/scripts/deadline")

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

executable = r"R:\pipeline\networkInstall\natron\2.5.0\Natron\bin\NatronRenderer.exe"
script_path = os.path.join(os.getcwd(), 'exr2mov.py')


print("yo")

def __main__(*args):
    firstFrameFile = ""
    job = MonitorUtils.GetSelectedJobs()[0]
    inputFile = job.OutputDirectories[0]
    inputFile = os.path.join( inputFile, job.OutputFileNames[0] )
    inputFile = re.sub( "\?", "#", inputFile )
    firstFrameFile = FrameUtils.ReplacePaddingWithFrameNumber( inputFile, job.Frames[0] )
    trim = firstFrameFile[:-8]
    input_file= (trim + "####.exr").replace("\\", "/")
    output_file =  (trim + "_preview.mov").replace("\\", "/")

    directory, file = os.path.split(firstFrameFile)
    pattern = re.compile(r".*\.(\d+)\.exr")
    matches = [pattern.match(item) for item in os.listdir(directory)]
    frames = [int(match.group(1)) for match in matches if match is not None]
    if len(frames) > 1:
        range_val = "{0}-{1}".format(frames[0], frames[-1])
    elif len(frames) > 0:
        range_val= str(frames[0])

    #jobname =  os.path.basename(os.path.normpath(job.OutputDirectories[0]))+"_denoiseJob"
    print("Output file: " +firstFrameFile)
    print ("frame_range="+range_val)

    # Set your parameters here
    command = f"output_file=\"{output_file}\";input_file=\"{input_file}\""


    bat_file_path = r'R:\pipeline\pipe\nuke\exr2mov\data\exr2mov_deadline.bat'  # replace with your .bat file path

    subprocess.Popen([bat_file_path, input_file, output_file, range_val])


# Rudimentary, just uses the smallest and greatest frame numbers that match the pattern
def populate_frame_list():
    directory, file = os.path.split(dialog.GetValue("InputPattern"))
    pattern = re.compile(r".*\.(\d+)\.exr")
    matches = [pattern.match(item) for item in os.listdir(directory)]
    frames = [int(match.group(1)) for match in matches if match is not None]
    if len(frames) > 1:
        frame_range = "{0}-{1}".format(frames[0], frames[-1])
        dialog.SetValue("Frames", frame_range)
    elif len(frames) > 0:
        dialog.SetValue("Frames", str(frames[0]))


def populate_output_path():
    input_pattern = dialog.GetValue("InputPattern")
    pattern = re.compile(r"(.*\d+)\.exr")
    match = pattern.match(input_pattern)
    if match is not None:
        output_pattern = "{0}_denoised.exr".format(match.group(1))
        dialog.SetValue("OutputPattern", output_pattern)
