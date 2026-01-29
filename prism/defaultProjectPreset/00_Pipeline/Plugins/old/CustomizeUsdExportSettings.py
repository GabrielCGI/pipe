# CustomizeUsdExportSettings.py
import os

name = "CustomizeUsdExportSettings"
classname = "CustomizeUsdExportSettings"


class CustomizeUsdExportSettings:
    def __init__(self, core):

        self.core = core
        self.version = "v1.0.1"
        if self.core.appPlugin.pluginName not in ["Maya"]:
              return
        self.core.registerCallback("preMayaUSDExport", self.preMayaUSDExport, plugin=self)

        print("CustomizeUsdExportSettings loaded. Set eulerFilter")

    def getExportedObject(self):
        core = self.core
        sm = core.getStateManager()
        try:
            assetName = core.entities.getCurrentScenefileData()['asset']
        except:
            assetName = ''
        
        print('assetname is : '+assetName)
        for state in sm.states:
            print(state)
            if state.ui.className == "USD Export":
                objects = state.ui.nodes
                print(objects)
                
                if not objects:
                    print('codeOut')
                    continue
            
                child = objects[0].split('|')[-1]
                print(child)

                if child == assetName:
                    print('success finding child')
                    return child

    def getProductName(self):
        core = self.core
        sm = core.getStateManager()

        subFrame = 0
        for state in sm.states:
            print(state)
            if state.ui.className == "USD Export":
                productName = state.ui.getProductname()
                print(productName)
                try:
                    productName = productName.split('_')[-1]
                except:
                    None
                
                if not productName:
                    print('codeOut')
                    subFrame = 0
                    continue

                if productName == 'animSubFrame':
                    subFrame = 1
                else:
                    subFrame = 0
                
        return subFrame

    def preMayaUSDExport(self, origin, options, outputPath):

        core = self.core
        newVal = "eulerFilter=1"
        
        if "eulerFilter" in options:
            idx = options.find("eulerFilter")
            rplStr = options[idx:idx+len("eulerFilter")+2]
            options = options.replace(rplStr, newVal)
            print(options)
        
        else:
            options +=  ";"+  newVal + ";"
        
        
        child = self.getExportedObject()

        if child:
            
            defaultPrim = 'defaultPrim='+child
          

            if 'defaultPrim' in options:
                idx = options.find("defaultPrim")
                rplStr = options[idx:idx+len("defaultPrim")+2]
                options = options.replace(rplStr, defaultPrim)
                print(options)

            else:
                
                options +=  ";"+ defaultPrim +';'
                
        subFrame = self.getProductName()
        print(subFrame)

        if subFrame == 1:

            frameSample = 'frameSample=-0.3 -0.2 -0.1 0 0.1 0.2 0.3'
            
            if 'frameSample' in options:
                idx = options.find("frameSample")
                rplStr = options[idx:idx+len("frameSample")+2]
                options = options.replace(rplStr, frameSample)
                print(options)

            else:
                
                options +=  ";"+ frameSample +';'





        return {"options": options}

    