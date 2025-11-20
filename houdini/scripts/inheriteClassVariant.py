from pxr import Sdf, Usd, Kind, UsdGeom
from datetime import datetime
from pathlib import Path
import socket
import sys
import os
import re


DEBUG = 0
LIST_MACHINE_DEBUG = ["FALCON-01"]


class inheriteClassAttr():
    def __init__(self, filePathImport, soft, clearFile=False):
        if not os.path.exists(filePathImport):
            print("no file found")
            return 
        
        self.result = True
        self.soft = soft
        if self.soft == "Houdini":
            import hou
            self.message = "Everything went well\nReload Prism Import"
            self.error_type = hou.severityType.Message
        elif self.soft == "Maya":
            self.message = "inherite Class:\nEverything went well"
            self.error_type = "info"

        
        self.filePathImport = str(Path(filePathImport))
        self.projet = "/".join(self.filePathImport.split("\\")[:2])
        self.clearFile = clearFile
        self.prefix = "CLEAR" if clearFile else "ADD"
        self.NewLayer = None
        self.root = None
        self.NameFolder = "_layer_anm_class"
        self.run()
        
    def debugger(self):
        if socket.gethostname() in LIST_MACHINE_DEBUG:
            sys.path.append("R:/pipeline/networkInstall/python_shares/python311_debug_pkgs/Lib/site-packages/debug")
            import debug
            debug.debug()
            debug.debugpy.breakpoint()

    def sendError(self, msg, type):
        self.message = msg
        print(msg)
        if self.soft == "Houdini":
            import hou # type: ignore
            if type == "error":
                self.error_type = hou.severityType.Error
            elif type == "warning":
                self.error_type = hou.severityType.Warning
            elif type == "importMessage":
                self.error_type = hou.severityType.ImportantMessage
            else:
                print("---------------blablabal")
            
        elif self.soft == "Maya":
            if type == "error":
                self.error_type = "error"
            elif type == "warning":
                self.error_type = "warning"
            elif type == "importMessage":
                self.error_type = "warning"
            else:
                print("---------------blablabal")
        
        self.result = False


    def run(self):
        print("openning file.....")
        try:
            stage = Usd.Stage.Open(self.filePathImport)
        except Exception as e:
            self.message = str(e)
            self.result = False
            return

        print("\nfind Good Layer.....")
        infoLay, layerPath, masterLayer, layersParsing = self.FindGoodLayer(stage, "/_layer_anm_main", "/_layer_anm_master/")
        if not infoLay or not layerPath:
            self.sendError('no layer "/_layer_anm_main/" found in this stack usd', "error")
            return

        
        newPath = self.createLayerClass(layerPath[0])
        if not newPath:
            self.sendError("inpossible to create /layer_anm_class/", "error")
            return
        
        print(f"\nCreate new layer  here: {newPath}")
        self.NewLayer = Usd.Stage.CreateNew(newPath)
        for layerParse in layersParsing:
            self.root = Usd.Stage.Open(layerParse)
            print(layerParse, self.NewLayer, self.root)



            print(f"\nadd subLayer in _layer_anm_master")
            self.AppendLayer(masterLayer, newPath)


            print("\n\nnow find charaters and props....")
            allPathPrim = self.getAllPrimPath(self.root, ["/assets/props/", "/assets/propsSkin/", "/assets/characters/"])
            if not allPathPrim:
                self.sendError("no props and no characters", "importMessage")
                return
            

            print(f"{self.prefix} USD-----------------------------------------------------------------------------------------------")
            if not self.clearFile:
                self.NewLayer.CreateClassPrim(f"/__class__")

        
            for prim in allPathPrim:
                if not prim.IsValid():
                    print("no valid", prim.GetPrimStack())
                    continue
                

                namePrim = prim.GetName()
                if not self.clearFile:
                    primReference, isProps = self.pathReference(namePrim)
                
                if not primReference:
                    self.sendError(f"warning {namePrim} prim reference not found\nfor the object: {namePrim}\nPrim path: {str(prim.GetPath())}", "importMessage")
                    continue

                print(f"\n{self.prefix} Set variant for:    ", namePrim, "---------------------------------------")
                self.setVariant(prim, primReference)

                print(f"\n{self.prefix} Inherit class for:  ", namePrim, "---------------------------------------")
                self.inheriteComponent(namePrim, prim)

                print(f"\n{self.prefix} Reference path for: ", namePrim, "---------------------------------------")
                if not self.clearFile:
                    self.addReferenceUSD(namePrim, primReference[3:], isProps)

                
                print("\n")



        print("\n\nsave file....")
        self.NewLayer.GetRootLayer().Save()
        print("inherite class finish.")
        return self.result

    def showAllChild(self, prim):
        imageable = UsdGeom.Imageable(prim)
        if imageable:
            name = prim.GetName().lower()
            if not "/characters/" in str(prim.GetPath()):
                over = self.NewLayer.OverridePrim(prim.GetPath())
                overImage = UsdGeom.Imageable(over)
                overImage.CreateVisibilityAttr().Set("inherited")

                """if "/characters/" in str(prim.GetPath()):
                    if name.startswith("proxy"):
                        over.CreateAttribute("purpose", Sdf.ValueTypeNames.Token, custom=True).Set("proxy")
                    elif name.startswith("brushes"):
                        over.CreateAttribute("purpose", Sdf.ValueTypeNames.Token, custom=True).Set("render")"""


        for child in prim.GetChildren():
            self.showAllChild(child)
    
    def compareWithSource(self, refPrim):
        ref = Usd.Stage.Open(refPrim)
        for primRef in ref.Traverse():
            getVarRef = primRef.GetVariantSets().GetVariantSet("geo").GetVariantNames()
            if getVarRef:
                break
        
        return getVarRef

    def showProxyAndRender(self, prim):
        imageable = UsdGeom.Imageable(prim)
        if imageable:
            if not "/characters/" in str(prim.GetPath()):
                for purpose in ["render", "proxy"]:
                    over_proxy = self.NewLayer.OverridePrim(str(prim.GetPath()) + "/geo/" + purpose)
                    overImage = UsdGeom.Imageable(over_proxy)
                    overImage.CreateVisibilityAttr().Set("inherited")

    def setVariant(self, prim, refPrim):
        path = prim.GetPath()
        visible, hidden = self.getVariant(path)
        if not visible and not hidden:
            print("not virant")
            return
        getVarRef = self.compareWithSource(refPrim)
        if not hidden and not getVarRef:
            self.showProxyAndRender(prim)
            print("there are no variant")
            return
        if not visible and hidden:
            print("_|_|_| WARNING |_|_|_ Shape hide in maya")
            return
        

        if len(visible) >=2:
            print("_|_|_| WARNING |_|_|_ multiple variant in: ", visible)
        
        self.showAllChild(prim)
        variant = visible[0]
        

        if not getVarRef:
            print("_|_|_| WARNING |_|_|_ not variant found")
            return
        
        if not variant in getVarRef:
            print("_|_|_| WARNING |_|_|_ not same variant beteewn usdClass and Rig", getVarRef, visible)
            print("set default variant:", getVarRef[0])
            variant = getVarRef[0]
        
        
        over = self.NewLayer.OverridePrim(prim.GetPath())
        geo_variant_set = over.GetVariantSet("geo")
        geo_variant_set.AddVariant(variant)
        geo_variant_set.SetVariantSelection(variant)
        print("variant set:", variant)
        
    def getVariant(self, path):
        #self.debugger()
        xform_prim = self.root.GetPrimAtPath(f"{path}/geo/render/xform")
        if not xform_prim.IsValid():
            xform_prim = self.root.GetPrimAtPath(f"{path}/geo/proxy/xform")
            if not xform_prim.IsValid():
                return None, None
        

        visible = []
        hidden = []
        for child in xform_prim.GetChildren():
            geom = UsdGeom.Imageable(child)
            vis = geom.GetVisibilityAttr().Get()
            if vis == "inherited":
                visible.append(child.GetName())
            else:
                hidden.append(child.GetName())
        
        return visible, hidden

    def createLayerClass(self, path):
        pathSplit = path.split("\\")[:-3]
        seq = pathSplit[-3]
        shot = pathSplit[-2]

        new_path = "\\".join(pathSplit)
        if not os.path.exists(new_path):
            return None
        
        folder = new_path + "\\" + self.NameFolder
        if not os.path.exists(folder):
            os.mkdir(folder)
        
        version, Vint = self.FindLastVersion(folder)
        if not version:
            version = "v001"
        else:
            version = "v" + str(Vint + 1).zfill(3)


        folderversion = folder + "\\" + version
        os.mkdir(folderversion)
        newFilePath = folderversion + f"\\{seq}-{shot}_{self.NameFolder}_{version}.usda"

        return newFilePath

    def FindGoodLayer(self, root, layerName_main, layerName_master):
        used_layers = root.GetUsedLayers()
        layerFilePath = []
        infoLay = None
        layerPath = []
        layerMaster = None
        for layer in used_layers:
            if layerName_main in layer.identifier and not "Assets" in layer.identifier:
                infoLay = layer.identifier.split("/")[-1]
                layerFilePath.append(layer.identifier)
                layerPath.append(layer.realPath)
            elif layerName_master in layer.identifier and not "Assets" in layer.identifier:
                layerMaster = layer
        
            """if layerMaster and layerPath and infoLay:
                break"""
        
        return infoLay, layerPath, layerMaster, layerFilePath

    def getAllPrimPath(self, stage, ListFinds):
        matchedPaths = []
        for find in ListFinds:
            alltraverse = None
            try:
                alltraverse = stage.Traverse()
            except:
                pass


            for prim in alltraverse:
                if not find in str(prim.GetPath()):
                    continue
                
                if prim.GetMetadata("kind") == "component":
                    matchedPaths.append(prim)
    
        return matchedPaths
    
    def pathReference(self, primName):
        pathUSD = None
        for element in ["Props", "Characters", "Sets"]:
            USD = "USD"
            if primName == "dishOmeletFull":
                primName =  "dishOmelet"
                USD = "dishOmeletFull"
            
            dosAsset = rf"{self.projet}/03_Production/Assets/{element}/{primName}/Export/{USD}"
            
            versionUSD = None
            isProps = None
            if not os.path.exists(dosAsset):
                continue


            lastVersion, _ = self.FindLastVersion(dosAsset)
            for filename in os.listdir(dosAsset + "/" + lastVersion):
                if filename.startswith(f"{primName}_{USD}_{lastVersion}.usd"):
                    versionUSD = filename
                elif filename.startswith("geo.usd"):
                    isProps = True
            
            pathUSD = rf"{self.projet}/03_Production/Assets/{element}/{primName}/Export/{USD}/{lastVersion}/{versionUSD}"
            if not os.path.exists(pathUSD):
                print("ERROR path not foud.........................")
                print(pathUSD)
                self.result = False
                pathUSD = None

            break
        return pathUSD, isProps

    def FindLastVersion(self, path):
        max_version = -1
        latest_file = None
        version = 0
        for filename in sorted(os.listdir(path)):
            if not filename or not filename.startswith("v"):
                continue

            v = re.findall(r'\d+', filename)[0]
            version = int(v)
            if version > max_version:
                max_version = version
                latest_file = filename

        return latest_file, version

    def inheriteComponent(self, primName, prim):
        over = self.NewLayer.OverridePrim(prim.GetPath())
        inheritPath = Sdf.Path(f"/__class__/{primName}")
        print(f"Inherit path: {inheritPath}")
        over.GetInherits().AddInherit(inheritPath, position=Usd.ListPositionFrontOfPrependList)

    def AppendLayer(self, layer, sublayer):
        ORlist = list(layer.subLayerPaths)
        for pathlayer in ORlist:
            if self.NameFolder in pathlayer:
                try:
                    layer.subLayerPaths.remove(pathlayer)
                except:pass
        

        sublayer = f"../../{self.NameFolder}/" + sublayer.split(f"\\{self.NameFolder}\\")[-1].replace("\\", "/")
        print("path append:", sublayer)
        layer.subLayerPaths.insert(0, sublayer)
        print(layer)
        layer.Save()

    def addReferenceUSD(self, primName, refPath, isProps):
        prim = self.NewLayer.CreateClassPrim(f"/__class__/{primName}")
        prim.SetInstanceable(False)
        Usd.ModelAPI(prim).SetKind(Kind.Tokens.component)
        data = prim.GetReferences()
        data.ClearReferences()
        if isProps:
            print(f"ref prim: /geo")
            data.AddReference(refPath, Sdf.Path(f"/{primName}"), position=Usd.ListPositionFrontOfPrependList)
        else:
            print(f"prim geo not valide convert Prim: /{primName}")
            data.AddReference(refPath, Sdf.Path(f"/{primName}"), position=Usd.ListPositionFrontOfPrependList)
            