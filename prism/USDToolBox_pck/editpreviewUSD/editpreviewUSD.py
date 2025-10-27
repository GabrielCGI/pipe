from datetime import datetime
from pxr import Sdf, Usd

import shutil
import os 



class EditPreviewUSD():
    def __init__(self, usdFolder, core=None):
        self.core = core
        
        fileMTL = os.path.join(usdFolder, "mtl.usdc")
        if not os.path.exists(fileMTL):
            self.superPrint("file not found", True, "warning")
            return None
                
        self.supperMESSAGE = ""
        shader_names = []
        materials = []
        Error = False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = f"{fileMTL}.{timestamp}.bak"
        shutil.copy2(fileMTL, backup)

        file_mtl = Sdf.Layer.FindOrOpen(fileMTL)
        for prim in file_mtl.rootPrims:
            if prim.specifier != Sdf.SpecifierOver:
                continue
            
            self.superPrint("return list mat and shaders----------")
            materialMtlPath = self.getMaterialAndShaders(prim, file_mtl, materials, shader_names)


            self.superPrint("\ntry to remove connection on roughness----------")
            for mat in materials:
                primMaterial = file_mtl.GetPrimAtPath(Sdf.Path(f"{materialMtlPath.path}/{mat}"))
                for shd in shader_names:
                    primShader = file_mtl.GetPrimAtPath(Sdf.Path(f"{materialMtlPath.path}/{mat}/{shd}"))
                    if not primShader:
                        continue
                    
                    if "_preview_" in shd and "roughness" in shd:
                        self.superPrint(f"remove {primShader.path}")
                        del primMaterial.nameChildren[shd]


                    elif shd.endswith("_preview"):
                        self.superPrint(f"modif value roughness--------------\n    {primShader.path}")
                        attr = primShader.attributes.get("inputs:roughness")
                        if not attr:
                            attr = Sdf.AttributeSpec(primShader, "inputs:roughness", Sdf.ValueTypeNames.Float, Sdf.VariabilityVarying)
                        attr.default = 0.4

                        self.superPrint(f"disconnet roughness--------------\n    {primShader.path}\n")
                        attr.connectionPathList.ClearEdits()
            

        if not Error:
            file_mtl.Save()
            self.superPrint(f'{fileMTL}\nedit finish, file saved', True, "info")
        else:
            self.superPrint('une erreur est survenue', True, "error")

    def getMaterialAndShaders(self, prim, file, materials, shader_names):
        primAssetPath = None
        PrimOVERAssetsPath = None
        variant = True
        for primchild in prim.nameChildren.values():
            self.superPrint(primchild)
            if str(primchild.path).endswith("/ASSET"):
                primAssetPath = primchild
            else:
                PrimOVERAssetsPath = primchild.name

        if not primAssetPath or not PrimOVERAssetsPath: self.superPrint('is not a variant');variant = False
        
        materialMtlPath = None
        if variant:
            materialMtlPath = file.GetPrimAtPath(Sdf.Path(f"{prim.path}/{PrimOVERAssetsPath}/mtl"))
        else:
            materialMtlPath = file.GetPrimAtPath(Sdf.Path(f"{prim.path}/{PrimOVERAssetsPath}"))
        
        if not materialMtlPath:
            return None
        

        for child in materialMtlPath.nameChildren.values():
            materials.append(child.name)
            for shader in child.nameChildren.values():
                if not shader.name in shader_names and "_preview" in shader.name:
                    shader_names.append(shader.name)
        
        return materialMtlPath

    def superPrint(self, txt, force=False, typ = "info"):
        if self.core and force:
            self.core.popup(txt, severity=typ)
        else:
            print(txt)