from Deadline.Events import DeadlineEventListener
from Deadline.Scripting import *
import os
import re
import sys
import requests
import json
import random
import tempfile
import subprocess
import logging
import datetime
from pathlib import Path

PYTHON = r'R:\pipeline\networkInstall\python\Python310\python.exe'
LOG_DIR = r'R:\devmaxime\discordbot\logs'
LOG = None

def setupLog(usdfile: str):
    """Setup LOG basic config.

    Args:
        usdfile (str): USD path.
    """
    global LOG
    global LOG_FILE
    
    basename = os.path.basename(usdfile)
    name = os.path.splitext(basename)[0]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    logname = sorted(Path(LOG_DIR).glob(f'log_{name}_*.txt'))
    
    if logname:
        LOG_FILE = logname[0]
    else:
        logfilename = f"log_{name}_{timestamp}.txt"
        LOG_FILE = os.path.join(LOG_DIR, logfilename)

    os.makedirs(LOG_DIR, exist_ok=True)
    
    LOG = logging.getLogger(f"PrismPostExport_{name}")
    LOG.setLevel(logging.INFO)

    LOG.propagate = False

    if LOG.hasHandlers():
        LOG.handlers.clear()

    file_handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    
    LOG.addHandler(file_handler)
    

def GetDeadlineEventListener():
    """
    This is the function that Deadline calls to get an instance of the
    main DeadlineEventListener class.
    """
    return PublishDiscord()

def CleanupDeadlineEventListener(deadlinePlugin):
    """
    This is the function that Deadline calls when the event plugin is
    no longer in use so that it can get cleaned up.
    """
    deadlinePlugin.Cleanup()

class PublishDiscord(DeadlineEventListener):
    """
    This is the main DeadlineEventListener class for MyEvent
    """
    def __init__(self):
        # Set up the event callbacks here
        super().__init__()
        self.OnJobFinishedCallback += self.OnJobFinished

    def Cleanup(self):
        del self.OnJobFinishedCallback

    def __submit_discord_publish(self, job):
        """
        Add a Discord message
        """
        # Get the discord user by getting the deadline user and a matching dictionary
        job_name = job.JobName
        user_list = self.GetConfigEntry("DiscordUserAccount").split(";")
        user = None
        for user_line in user_list:
            user_pair = user_line.split(":")
            if user_pair[0] == job.JobUserName:
                user = user_pair[1]
                break
        # Get some values to display in the discord message
        comment = job.JobComment
        nb_frame = len(job.Frames)
        first_frame = min(job.Frames)
        last_frame = max(job.Frames)
        frames = str(first_frame)+"-"+str(last_frame)
        days = str(job.TotalRenderTime.Days).zfill(2)
        hours = str(job.TotalRenderTime.Hours).zfill(2)
        minutes = str(job.TotalRenderTime.Minutes).zfill(2)
        seconds = str(job.TotalRenderTime.Seconds).zfill(2)
        render_time = days + ":" + hours + ":" + minutes + ":" + seconds
        submit_time = job.JobSubmitDateTime.ToString()
        avg_time = job.AverageTaskTime
        LOG.info(avg_time)
        end_time = job.JobCompletedDateTime.ToString()
        error_count = job.ErrorReports
        # Get a random message within a list of premade ones
        message_list = self.GetConfigEntry("MessageList").split(";")
        rand_num_msg = random.randint(0,len(message_list)-1)
        description = message_list[rand_num_msg]
        # Get the discord server and the channel matching the current project
        server_pub = self.GetConfigEntry("DiscordServer")
        channel_pub = None
        project_name = job.GetJobEnvironmentKeyValue("CURRENT_PROJECT")
        project_channels = self.GetConfigEntry("DiscordProjectChannelList").split(";")
        if project_name is not None :
            for project_channel in project_channels:
                project_pair = project_channel.split(":")
                if project_pair[0] == project_name:
                    channel_pub = project_pair[1]
                    break
        if channel_pub is None :
            channel_pub = self.GetConfigEntry("DefaultDiscordChannel")
        video_path = job.JobExtraInfo0 if os.path.exists(job.JobExtraInfo0) else None
        datas = {
            "job_name":job_name,
            "user":user,
            "comment":comment,
            "frames":frames,
            "submit_time":submit_time,
            "end_time":end_time,
            "render_time":render_time,
            "avg_time":avg_time,
            "error_count":error_count,
            "description":description,
            "video":video_path,
            "server_pub":server_pub,
            "channel_pub":channel_pub
        }

        # Write datas to a temp file
        tmp = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
        tmp.writelines(json.dumps(datas))
        tmp.close()

        # Launch with python >3.7 (here mayapy)
        python_path = "\"" + PYTHON.replace("\\","/") + "\""
        publish_discord_script = r"R:\deadline\custom\events\PublishDiscord\publish_discord_script.py".replace("\\","/")
        tmp_filename = tmp.name
        command =  'python' +" "+ publish_discord_script+ " "+tmp_filename

        os.system(f"\"{command}\"")
        os.remove(tmp_filename)


    def OnJobFinished(self, job):
        """
        On Job finished launch Noice
        """
        match = re.match(r"^(.*)--no-pub-dc(.*)$",job.JobComment)
        
        if match:
            setupLog('Unpublished')
            LOG.info('No publish. To publish automatically to discord remove --no-pub-dc to the comment of your job')
            print("No publish. To publish automatically to discord remove --no-pub-dc to the comment of your job")
            return
        setupLog(job.JobName)
        LOG.info('Job published')
        self.__submit_discord_publish(job)
