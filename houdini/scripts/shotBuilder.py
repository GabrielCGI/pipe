import hou #type: ignore
import json



try:
    import PrismInit #type: ignore
except:
    usdPlug = None
else:
    usdPlug = PrismInit.pcore.getPlugin("USD")

if usdPlug:
    usdImport = usdPlug.api.usdImport



class ShotBuilder():
    def __init__(self, selection, shots: list[str], UI=True):
        self.seqName = "shot"
        self.result = True
        self.message = ""
        self.all_msg = ""
        self.spacer = 15

        if not selection:
            self.sendError("Select what you want duplicate", "importMessage")
            return
        
        if not shots:
            self.sendError("no shot to build found", "Message")
            return


        self.createContextoptions(shots)

        for parition in selection:
            self.renameAndSetNodes(parition.items(), f"{self.seqName}_{str(shots[0])}", 0)
        del shots[0]

        for i, shot in enumerate(shots):
            for parition in selection:
                if parition.__class__ != hou.OpNetworkBox:
                    print(parition, " is not a NetworkBox")
                    continue
                
                self.duplicatePartition(parition, f"{self.seqName}_{shot}", i + 1)
        
        if self.all_msg:
            self.sendError("two nodes with same name:\n" + self.all_msg, "importMessage")
            return

    def sendError(self, msg, type):
        self.message = msg
        print(msg)

        if type == "error":
            self.error_type = hou.severityType.Error
        elif type == "warning":
            self.error_type = hou.severityType.Warning
        elif type == "importMessage":
            self.error_type = hou.severityType.ImportantMessage
        elif type == "Message":
            self.error_type = hou.severityType.Message
        else:
            print("---------------blablabal")
        
        self.result = False

    def duplicatePartition(self, box: hou.OpNetworkBox, name_shots: str, iteration: int) -> str:
        parent_stage = hou.node("/stage")
        sel_before = set(hou.selectedItems())
        parent_stage.copyNetworkBox(box, new_name="SHOT_EDITS")
        sel_after = set(hou.selectedItems())
        diff = list(sel_after - sel_before)
        if not diff:
            return
        
        node = diff[0]
        anti = 0
        while node or anti <=20: 
            parent = node.parentNetworkBox()
            if not parent:
                break
            node = parent
            anti +=1

        node.setPosition([node.position()[0] + self.spacer*iteration, node.position()[1]])
        self.renameAndSetNodes(diff, name_shots, iteration)

    def renameAndSetNodes(self, listNodes: list, name_shots: str, iteration):
        for node in listNodes:
            if node.__class__ == hou.OpStickyNote:
                node.setText(name_shots)

            if not node.__class__ == hou.LopNode:
                continue

            parm = node.parm("toRename")
            if not parm:
                continue
            to_rename = parm.eval()


            if node.type().name() == "editcontextoptions":
                node.parm("optionstrvalue1").set(name_shots)
            elif node.type().name() == "null" and to_rename == "":
                hou.node("/stage/switch_importShots").setInput(iteration, node)
            elif node.type().name() == "null" and to_rename == "_OUT":
                hou.node("/stage/switch_shotsEdits").setInput(iteration, node)
            elif node.type().name() == "prism::LOP_Import::1.0" and usdImport:
                self.importLastStackUSDinShot(node, name_shots.replace(f"{self.seqName}_", ""))

            try:
                node.setName(name_shots + to_rename)
            except Exception as e:
                self.all_msg += f"-> impossible to rename: {node.name()}\n"
                continue

            if to_rename == "_FetchLightCache":
                node.parm("loppath").set(f"../{name_shots}_LightingCache")
            elif to_rename == "_FetchLightingLive":
                node.parm("loppath").set(f"../{name_shots}_Lighting")

    def createContextoptions(self, shots):
        hou.setContextOption("layer", "Layer")
        layers = [["VOLUME", "VOLUME"], ["MG", "MG"], ["BG", "BG"], ["FG", "FG"], ["CHARS", "CHARS"]]
        hou.setContextOptionConfig("layer", config=json.dumps({"menu_items": layers, "label": "Layer", "type": "string_menu"}))

        hou.setContextOption("lightCache", "Light Caching")
        hou.setContextOptionConfig("lightCache", config=json.dumps({"menu_items": [["Light Live", 0], ["Light Cached", 1]], "label": "Light Caching", "type": "int_menu"}))

        hou.setContextOption("shot", "Shot")
        hou.setContextOptionConfig("shot", config=json.dumps({"menu_items": [[f"shot_{shot}", f"shot_{shot}"] for shot in shots], "label": "Shot", "type": "string_menu"}))

    
    def importLastStackUSDinShot(self, node, shot):
        path = usdPlug.api.getLatestEntityUsdPath({"shot": shot, "type": "shot"})
        if path:
            node.parm("filepath").set(path)