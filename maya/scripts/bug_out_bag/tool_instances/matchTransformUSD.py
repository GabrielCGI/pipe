from ..tool_models.MultipleActionTool import *
from mayaUsd.lib import proxyAccessor as pa
from pxr import Sdf, UsdGeom ,Usd, Gf
import mayaUsd
import maya.cmds as cmds
import math

class MatchTransform(MultipleActionTool):
    def __init__(self):
        actions = {
            "MatchAll": {
                "text": "match ALL",
                "action": lambda nul: self.run("ALL"),
                "row": 0
            },
            "MatchTR": {
                "text": "match Translate",
                "action": lambda nul: self.run("translate"),
                "row": 1
            },
            "MatchRO": {
                "text": "match Rotate",
                "action": lambda nul: self.run("rotateXYZ"),
                "row": 1
            },
            "MatchSC": {
                "text": "match Scale",
                "action": lambda nul: self.run("scale"),
                "row": 1
            }
        }
        tooltip = "Match Transform USD"
        super().__init__(
            name="Match Transform USD",
            pref_name="match_transform_usd",
            actions=actions, stretch=1, tooltip=tooltip)
        
    def findPrim(self):
        stagePath, sdfPath = pa.getSelectedDagAndPrim()
        if not stagePath:
            return None
        
        stage = mayaUsd.ufe.getStage(stagePath)
        prim = stage.GetPrimAtPath(Sdf.Path(sdfPath))
        
        return prim

    def openStageGetPrim(self, pathFile, pathPrim):
        stage = Usd.Stage.Open(pathFile)
        prim = stage.GetPrimAtPath(pathPrim)
        if not prim.IsValid():
            print("Invalid prim:", prim.GetPath())
        
        return prim

    def run(self, transform = "ALL"):
        sel = cmds.ls(sl=True)
        prim  = self.findPrim()
        if not prim or not sel:
            return cmds.inViewMessage(amg='select in first the prim an after the maya object', pos='midCenter', fade=True, bkc='0x323232')
        
        xformable = UsdGeom.Xformable(prim)
        ops = xformable.GetOrderedXformOps()
        if len(ops) < 3:
            print('no value')
            layerStack = prim.GetPrimStack()
            for spec in layerStack:
                if "_lay_" in spec.layer.identifier:
                    print("find")
                    #prim = openStageGetPrim(pathStage, str(spec.path))

        world_mat =  xformable.ComputeLocalToWorldTransform(Usd.TimeCode(cmds.currentTime(q=True)))
        self.PrintM4d(prim, world_mat)

        if transform == "ALL":
            self.copyTranslate(sel, world_mat.ExtractTranslation())
            self.copyRotation(sel, world_mat.ExtractRotation())
            self.copyScale(sel, world_mat.ExtractRotationMatrix())

        elif transform == "translate":
            self.copyTranslate(sel, world_mat.ExtractTranslation())
        elif transform == "rotateXYZ":
            self.copyRotation(sel, world_mat.ExtractRotation())
        elif transform == "scale":
            self.copyScale(sel, world_mat.ExtractRotationMatrix())
            
    def PrintM4d(self, other, matrix):
        fmt = f"{{:10.3f}}"
        print("---------- ", other, " ----------")
        for row in range(4):
            print("[", fmt.format(matrix[row][0]), fmt.format(matrix[row][1]), fmt.format(matrix[row][2]), fmt.format(matrix[row][3]), "]")
            
        print("---------- ", other, " ----------\n")


    def copyTranslate(self, sel, value):
        if not value:
            return print("no translate value found")

        cmds.xform(sel, t=value, ws=True)
        print('copy translate')

    def copyRotation(self, sel, value):
        if not value:
            return print("no rotate value found")
        
        rot_matrix = Gf.Matrix3d().SetRotate(value)
        y = -math.asin(rot_matrix[0][2])
        cos_y = math.cos(y)
        x = math.atan2(rot_matrix[1][2] / cos_y, rot_matrix[2][2] / cos_y)
        z = math.atan2(rot_matrix[0][1] / cos_y, rot_matrix[0][0] / cos_y)
        euler_rad = tuple(math.degrees(a) for a in (x, y, z))

        cmds.xform(sel, ro=euler_rad, ws=True)
        print('copy rotate')

    def copyScale(self, sel, value):
        if not value:
            return print("no scale value found")
        
        scale = Gf.Vec3d(*(v.GetLength() for v in value))
        cmds.xform(sel, s=scale, ws=True)
        print('copy scale')