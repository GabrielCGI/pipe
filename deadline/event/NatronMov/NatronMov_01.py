from Deadline.Plugins import *
from System.Diagnostics import *
import re
import os.path
import os

def __main__(*args):
    # Do test stuff
    print("plugin")
    pass


def GetDeadlinePlugin():
    return NatronMovPlugin()


def CleanupDeadlinePlugin(plugin):
    plugin.cleanup()


class NatronMovPlugin (DeadlinePlugin):
    def __init__(self):
        self.InitializeProcessCallback += self.initialize_process
        self.RenderExecutableCallback += self.render_executable
        self.RenderArgumentCallback += self.render_argument

    def cleanup():
        for handler in self.StdoutHandlers:
            del handler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback

    def initialize_process(self):
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple

        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.StdoutHandling = True
        self.PopupHandling = False

        self.AddStdoutHandlerCallback('ERROR:(.*)').HandleCallback += self.handle_stdout_error

    def handle_stdout_error(self):
        self.FailRender('Detected an error: ' + self.GetRegexMatch(1))

    # Figure out how to get the number of times this has been called
    def handle_stdout_progress(self):
        self.SetProgress(self.GetJob().GetJobInfoKeyValue('ChunkSize'))

    def render_executable(self):
        return self.GetConfigEntry('NatronRenderExecutable')

    def render_argument(self):
        start = self.GetStartFrame()
        end = self.GetEndFrame()

        #BLOOM_EDIT
        myPath= self.path_for_frame(self.GetPluginInfoEntry('InputPattern'), start)
        arguments = arguments.format(start,end)

        return arguments


