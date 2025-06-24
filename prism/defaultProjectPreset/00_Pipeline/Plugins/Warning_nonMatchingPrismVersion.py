# Warning_nonMatchingPrismVersion.py

import getpass
import re

name = "Warning_nonMatchingPrismVersion"
classname = "Warning_nonMatchingPrismVersion"


class Warning_nonMatchingPrismVersion:
    def __init__(self, core):
        self.core = core
        self.version = "v1.0.0"

        #if getpass.getuser() != "v.dornel":
        #    return
            
        self.core.registerCallback("onProjectBrowserStartup", self.onProjectBrowserStartup, plugin=self)
        self.core.registerCallback("onProjectChanged", self.onProjectChanged, plugin=self)
        self.core.registerCallback("onSceneOpen", self.onSceneOpen, plugin=self)

    def parse_version(self, version_str):
        return tuple(map(int, version_str.split('.')))

    def checkVersions(self):
            # cleaning version string
            raw_prism_version = self.core.version
            prism_version = self.parse_version(re.sub(r'[^0-9.]', '', raw_prism_version))
            

            raw_project_version = self.core.getConfig("globals", "prism_version", configPath=self.core.prismIni)
            project_version = self.parse_version(re.sub(r'[^0-9.]', '', raw_project_version))

            # force min version to 2.0.14
            if project_version < self.parse_version("2.0.14"):
                project_version = self.parse_version("2.0.14")
                
            # check if matching
            if prism_version < project_version:
                myprint="Vos versions de Prism ne correspondent pas au projet! \n"
                myprint +=(f"Version de Prism Loadé : {raw_prism_version} \n")
                myprint +=(f"Version du projet : {raw_project_version} (projet {self.core.projectName}\n")
                myprint +=(f"Allez voir avec quelqu'un de la tech pour voir ce qu'il se passe!\n")
                self.core.popup(myprint, severity="error")
            else:
                pass

    def onProjectBrowserStartup(self, origin):
        self.checkVersions()

    def onProjectChanged(self, *args):
        self.checkVersions()
    
    def onSceneOpen(self, *args):
        self.checkVersions()

if __name__ == '__main__':

    #Debug mode only : 

    import sys
    sys.path.append(r"C:\ILLOGIC_APP\Prism\2.0.16\app\Scripts")

    import PrismCore
    core = PrismCore.create(prismArgs=["noUI"])

    # use this if you want to load the previously active project
    core = PrismCore.create(prismArgs=["noUI", "loadProject"])

    print(f"pcore version: {core.version}")

    path = r"I:\Guerlain_Xmas25"
    core.changeProject(path)

    print(core.projectName)
    print(core.projectPath)
    project_version = core.getConfig("globals", "prism_version", configPath=core.prismIni)
    print(f"prjVersion : {project_version}")
    