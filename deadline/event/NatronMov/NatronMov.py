from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *


def __main__(*args):
    # Do test stuff
    pass


def GetDeadlinePlugin():
    return NatronMovPlugin()


def CleanupDeadlinePlugin(plugin):
    plugin.cleanup()

class NatronMovPlugin(DeadlinePlugin):
    MyClassScopedVariable = 0

    def __init__(self):

        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument

    def Cleanup(self):

        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback

    def InitializeProcess(self):

        self.SingleFramesOnly = False  # Does this plugin support ranges? -> only one job for all frames
        self.PluginType = PluginType.Simple  # We aren't to managing a process

        self.UseProcessTree = True  # End the spawned process on slave exit
        self.StdoutHandling = True  # Actually watch the output. See below

        self.AddStdoutHandlerCallback("ERROR:.*").HandleCallback += self.HandleError

    def RenderExecutable(self):

        executable = self.GetConfigEntry('NatronRenderExecutable')
        return executable

    def RenderArgument(self):

        InputPattern = self.GetPluginInfoEntryWithDefault( "InputPattern", self.GetDataFilename() )
        OutputPattern = self.GetPluginInfoEntryWithDefault( "OutputPattern", self.GetDataFilename() )

        Frames = self.GetPluginInfoEntryWithDefault( "Frames", self.GetDataFilename() )
        start = Frames.split('-')[0]
        end = Frames.split('-')[1]
        hd = "n"

        return ( '%s %s %s %s %s' % (InputPattern, OutputPattern, start, end, hd) )

    def HandleError(self):
        self.FailRender('Detected an error: ' + self.GetRegexMatch(1))
