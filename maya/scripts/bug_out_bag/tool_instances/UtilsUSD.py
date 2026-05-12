from ..tool_models.MultipleActionTool import *
from mayaUsd.lib import proxyAccessor as pa
from pxr import Sdf, UsdGeom ,Usd, Gf
import maya.cmds as cmds
import mayaUsd
import math

class UtilsUSD(MultipleActionTool):
    def __init__(self):
        actions = {
            "create attribute USD on prim": {
                "text": "Create Auto attr USD prim",
                "action": self.addAutoAttr,
                "row": 0
            },
            "add Scope attr": {
                "text": "add Scope attr",
                "action": self.addScope,
                "row": 1

            },
            "add component attr": {
                "text": "add component attr",
                "action": self.addComponent,
                "row": 1
            },
            "add empty typeName attr": {
                "text": "add empty typeName attr",
                "action": self.addtypeNameAttr,
                "row": 2
            },
            "add empty kind attr": {
                "text": "add empty kind attr",
                "action": self.addKindAttr,
                "row": 2
            },
        }
        tooltip = "Utils USD"
        super().__init__(
            name="Utils USD",
            pref_name="Utils_USD",
            actions=actions, stretch=1, tooltip=tooltip)

    def addAutoAttr(self):
        sel = cmds.ls(sl=True)
        if not sel:
            cmds.warning("select the main DAGNode")
            return
        sel = sel[0]
        self.addKindAttr(sel, "component")
        for geo in cmds.listRelatives(sel, c=True):
            self.addtypeNameAttr(geo, "Scope")
            for rp in cmds.listRelatives(geo, c=True):
                self.addtypeNameAttr(rp, "Scope")


    def addtypeNameAttr(self, grp: str, typeName=""):
        if "USD_typeName" not in cmds.attributeInfo(grp, all=True):
            cmds.addAttr(grp, longName="USD_typeName", niceName="typeName", dataType="string")
        cmds.setAttr(grp + ".USD_typeName", typeName, type="string")

    def addKindAttr(self, grp: str, kind=""):
        if "USD_kind" not in cmds.attributeInfo(grp, all=True):
            cmds.addAttr(grp, longName="USD_kind", niceName="kind", dataType="string")
        cmds.setAttr(grp + ".USD_kind", kind, type="string")

    def addScope(self):
        sel = cmds.ls(sl=True)
        if not sel:
            cmds.warning("select a DAGNode")
            return

        for i in sel:
            self.addtypeNameAttr(i, "Scope")

    def addComponent(self):
        sel = cmds.ls(sl=True)
        if not sel:
            cmds.warning("select a DAGNode")
            return

        for i in sel:
            self.addKindAttr(i, "component")