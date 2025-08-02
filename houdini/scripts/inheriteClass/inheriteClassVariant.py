from pxr import Sdf, Usd, Kind, UsdGeom
from datetime import datetime
from pathlib import Path
import shutil
import os
import re


class inheriteClassAttr():
    def __init__(self, filePathImport, clearFile=False):
        if not os.path.exists(filePathImport):
            print("no file found")
            return
        
        self.filePathImport = str(Path(filePathImport))
        self.clearFile = clearFile
        self.prefix = "CLEAR" if clearFile else "ADD"
        self.projet = "/".join(self.filePathImport.split("\\")[:2])
        self.root = None
        self.NewLayer = None
        self.NameFolder = "_layer_anm_class"
        self.Restriction = self.FindFile(r"\00_Pipeline\CustomModules\Python\inheriteClassRestriction\restriction.json")
        self.run()

    def run(self):
        print("openning file.....")
        stage = Usd.Stage.Open(self.filePathImport)

        print("\nfind Good Layer.....")
        infoLay, layerPath, masterLayer = self.FindGoodLayer(stage, "/_layer_anm_main/", "/_layer_anm_master/")
        if not infoLay:
            print('!!ERROR!! no layer found in this stack usd')
            return
        print(layerPath)

        
        newPath = self.createLayerClass(layerPath)
        if not newPath:
            print("error new path invalide")
            return
        
        print(f"\nCreate new layer  here: {newPath}")
        self.NewLayer = Usd.Stage.CreateNew(newPath)
        self.root = Usd.Stage.Open(self.filePathImport)



        print(f"\nadd subLayer in _layer_anm_master")
        self.AppendLayer(masterLayer, newPath)


        print("\n\nnow find charaters and props....")
        allPathPrim = self.getAllPrimPath(self.root, ["/assets/props/", "/assets/characters/"])
        if not allPathPrim:
            print("no props and no characters")
            return
        

        print(f"{self.prefix} USD-----------------------------------------------------------------------------------------------")
        self.NewLayer.RemovePrim("/__class__")
        if not self.clearFile:
            self.NewLayer.DefinePrim("/__class__", "Xform")

       
        for prim in allPathPrim:
            if not prim.IsValid():
                print("no valid", prim.GetPrimStack())
                continue
            

            namePrim = prim.GetName()
            if not self.clearFile:
                primReference, isProps = self.pathReference(namePrim)
            
            if not primReference:
                print("error ", primReference, namePrim, "prim reference not found")
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

        print("nice your publish is finish :)")


    def showAllChild(self, prim):
        imageable = UsdGeom.Imageable(prim)
        if imageable:
            name = prim.GetName().lower()
            over = None
            if not self.checkRestriction(self.Restriction["notAfect"], name):
                
                if not over:
                    over = self.NewLayer.OverridePrim(prim.GetPath())
                overImage = UsdGeom.Imageable(over)
                overImage.CreateVisibilityAttr().Set("inherited")
            else:
                print("cute", name)
            if "/characters/" in str(prim.GetPath()):
                if self.checkRestriction(self.Restriction["proxy"], name):
                    if not over:
                        over = self.NewLayer.OverridePrim(prim.GetPath())
                    over.CreateAttribute("purpose", Sdf.ValueTypeNames.Token, custom=True).Set("proxy")
                elif self.checkRestriction(self.Restriction["render"], name):
                    if not over:
                        over = self.NewLayer.OverridePrim(prim.GetPath())
                    over.CreateAttribute("purpose", Sdf.ValueTypeNames.Token, custom=True).Set("render")
                else:
                    print("pass", name)


        for child in prim.GetChildren():
            self.showAllChild(child)

    def setVariant(self, prim, refPrim):
        self.showAllChild(prim)
        
        path = prim.GetPath()
        visible, hidden = self.getVariant(path)

        if not visible and not hidden:
            print("not virant")
            return
        elif not hidden:
            print("there are no variant")
            return

        if len(visible) >=2:
            print("_|_|_| WARNING |_|_|_ multiple variant in: ", visible)
        
        
        variant = visible[0]
        ref = Usd.Stage.Open(refPrim)
        for primRef in ref.Traverse():
            getVarRef = primRef.GetVariantSets().GetVariantSet("geo").GetVariantNames()

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
        xform_prim = self.root.GetPrimAtPath(f"{path}/geo/render/xform")
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
        print("fdefefzfzz", version, Vint)
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
        self.filePathImport = None
        infoLay = None
        layerPath = None
        layerMaster = None
        for layer in used_layers:
            if layerName_main in layer.identifier and not "Assets" in layer.identifier:
                infoLay = layer.identifier.split("/")[-1]
                self.filePathImport = layer.identifier
                layerPath = layer.realPath
            elif layerName_master in layer.identifier and not "Assets" in layer.identifier:
                layerMaster = layer
        
            if layerMaster and layerPath and infoLay:
                break
        
        return infoLay, layerPath, layerMaster

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
            dosAsset = rf"{self.projet}/03_Production/Assets/{element}/{primName}/Export/USD"
            versionUSD = None
            isProps = None
            if not os.path.exists(dosAsset):
                continue


            lastVersion, _ = self.FindLastVersion(dosAsset)
            for filename in os.listdir(dosAsset + "/" + lastVersion):
                if filename.startswith(f"{primName}_USD_{lastVersion}.usd"):
                    versionUSD = filename
                elif filename.startswith("geo.usd"):
                    isProps = True
            
            pathUSD = rf"{self.projet}/03_Production/Assets/{element}/{primName}/Export/USD/{lastVersion}/{versionUSD}"
            if not os.path.exists(pathUSD):
                print("ERROR path not foud.........................")
                print(pathUSD)
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
        for pathlayer in layer.subLayerPaths:
            if self.NameFolder in pathlayer:
                layer.subLayerPaths.remove(pathlayer)
        

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
    


    def log(self, log):
        print(log)
    
    def FindFile(self, path):
        if not os.path.exists(self.projet + path):
            print("no restriction found")
            return {"render":{"start":[], "end":[], "middle":[]}, 
                    "proxy":{"start":[], "end":[], "middle":[]}, 
                    "notAfect":{"start":[], "end":[], "middle":[]}}

        import json
        with open(self.projet + path, "r") as f:
            datarestriction = json.load(f)
        
        return datarestriction

    def checkRestriction(self, rest, primName):
        for i in rest["start"]:
            if primName.startswith(i):
                return True
            
        for i in rest["end"]:
            if primName.startswith(i):
                return True
            
        for i in rest["middle"]:
            if i in primName:
                return True
        
        return False
        
         

