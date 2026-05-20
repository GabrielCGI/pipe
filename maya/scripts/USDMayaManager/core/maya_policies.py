import mayaUsd.lib as mayaUsdLib #type: ignore
import maya.cmds as cmds
from pxr import Usd, Sdf



class MayaPolices():
    def __init__(self):
        self.list_USDShape = self.getListProxyShape()
        self.proxy_selected = None
        self.stage = None

        if self.list_USDShape:
            self.stage = self.getStageUSD(self.list_USDShape[0])
            self.proxy_selected = self.list_USDShape[0]
    
    def selectPrim(self, prim_paths: list[str]) -> None:
        if not self.proxy_selected or not prim_paths:
            return
        ufe_paths = [f"{self.proxy_selected},{p}" for p in prim_paths]
        cmds.select(ufe_paths)

    def getStageUSD(self, proxy_shape: str) -> Usd.Stage:
        prim = mayaUsdLib.GetPrim(proxy_shape)
        if prim and prim.IsValid():
            return prim.GetStage()

        return None
    
    def getListProxyShape(self) -> None:
        return cmds.ls(type="mayaUsdProxyShape", long=True) or []
    
    def changeProxySelect(self, new_proxy: str)-> None:
        self.proxy_selected = new_proxy
        self.stage = self.getStageUSD()

    def getSublayer(self, layer: Sdf.Layer, sublayer_path: str) -> Sdf.Layer:
        name_layer = Sdf.ComputeAssetPathRelativeToLayer(layer, sublayer_path)
        return Sdf.Layer.Find(name_layer)

    def traverse(self) -> Usd.PrimRange:
        return self.stage.TraverseAll()

    def getPayloadPrims(self) -> list[Usd.Prim]:
        return [prim for prim in self.stage.TraverseAll() if prim.HasPayload()]
    
    def muteLayers(self, layers: list[str]) -> None:
        for lay in layers:
            if self.stage.GetRootLayer().identifier == lay:
                continue
            
            if Sdf.Layer.Find(lay):
                self.stage.MuteLayer(lay)
        
    def unmuteLayers(self, layers: list[str]) -> None:
        for lay in layers:
            if self.stage.GetRootLayer().identifier == lay:
                continue
            
            if Sdf.Layer.Find(lay):
                self.stage.UnmuteLayer(lay)

    def loadPayloads(self, prims_path: list[str]) -> None:
        session_layer = self.stage.GetSessionLayer()
        with Usd.EditContext(self.stage, session_layer):
            for path in prims_path:
                self.stage.Load(path)

    def unloadPayloads(self, prims_path: list[str]) -> None:
        session_layer = self.stage.GetSessionLayer()
        with Usd.EditContext(self.stage, session_layer):
            for path in prims_path:
                self.stage.Unload(path)

    def getTypeLayersPath(self, all_wants: str):
        def parseLayer(layer: Sdf.Layer):
            for sub_path in layer.subLayerPaths:
                name_layer = Sdf.ComputeAssetPathRelativeToLayer(layer, sub_path)
                sub_layer = Sdf.Layer.Find(name_layer)
                if not sub_layer:
                    continue

                for want in all_wants:
                    if want in name_layer:
                        layer_path.append(sub_layer.identifier)
                        break
                
                parseLayer(sub_layer)
        
        root_layer = self.stage.GetRootLayer()
        layer_path = []
        
        parseLayer(root_layer)
        return layer_path



    # -------------- preset pour mute les different departement en 1 clic --------------
    def muteLayerLighting(self, active_btn):
        layer_lighting = self.getTypeLayersPath(["_lgt_"])
        print(layer_lighting)
        if active_btn:
            self.muteLayers(layer_lighting)
        else:
            self.unmuteLayers(layer_lighting)

    def muteLayerFXCFX(self, active_btn):
        layer_FXCFX = self.getTypeLayersPath(["_fx_", "_cfx_"])
        if active_btn:
            self.muteLayers(layer_FXCFX)
        else:
            self.unmuteLayers(layer_FXCFX)
        
    def muteLayerAnimation(self, active_btn):
        layer_Animation = self.getTypeLayersPath(["_anm_"])
        if active_btn:
            self.muteLayers(layer_Animation)
        else:
            self.unmuteLayers(layer_Animation)
        
    def muteLayerLayout(self, active_btn):
        layer_layout = self.getTypeLayersPath(["_lay_", "_set_"])
        if active_btn:
            self.muteLayers(layer_layout)
        else:
            self.unmuteLayers(layer_layout)
        
    def muteLayerCameras(self, active_btn):
        layer_camera = self.getTypeLayersPath(["_camera"])
        if active_btn:
            self.muteLayers(layer_camera)
        else:
            self.unmuteLayers(layer_camera)
        

    
    
    # -------------- preset pour unload les different payloads en 1 clic --------------
    def traverseAllPayloadAtPath(self, start, noRecursive=False)-> list[Usd.Prim]:
        all_prims = []
        prim = self.stage.GetPrimAtPath(start)
        if prim is None:
            return []
        if not prim.IsValid():
            return []
        
        def parseChild(pimParent: Usd.Prim, all_prims: list, stop):
            if pimParent.HasPayload():
                all_prims.append(pimParent)
            if noRecursive and stop:
                return
            
            for child in pimParent.GetAllChildren():
                parseChild(child, all_prims, True)
        
        parseChild(prim, all_prims, False)
        
        return all_prims
    
    def unloadPayloadsLights(self, active_btn):
        self.unloadLoadPayload(active_btn, ["/"], "lights")

    def unloadLoadPayload(self, active: bool, data: list[str], have=None):
        to_unload = []
        for path_start in data:
            for pay in self.traverseAllPayloadAtPath(path_start):
                if have:
                    if have not in pay.GetPath().pathString:
                        continue
                print(pay)
                to_unload.append(pay.GetPath().pathString)
        
        print(to_unload, active)
        if active:
            self.unloadPayloads(to_unload)
        else:
            self.loadPayloads(to_unload)