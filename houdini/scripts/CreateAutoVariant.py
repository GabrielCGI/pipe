import hou
from pxr import Usd, UsdGeom


class autoVariant():
    def __init__(self):
        if len(hou.selectedNodes()) != 3:
            hou.ui.displayMessage("Select 3 nodes in this order: Prism LOP import / componentIN / componentOUT", buttons=("OK",) ,severity=hou.severityType.Error)
            return

        self.importLOP = hou.selectedNodes()[0]
        self.refDupi = hou.selectedNodes()[1]
        self.compOUT = hou.selectedNodes()[2]

        self.list_variant = []
        self.pasDecal = 2
        self.pasTrsDecal = 10
        self.mergeToRig = hou.node("/stage/merge4")
        self.mergeToSusbtance = hou.node("/stage/merge5")
        
        withVar = hou.ui.displayMessage("it's variant ?", buttons=("Yes", "No", "skip") , close_choice=2)
        if withVar == 2:
            return
        
        scenepath = hou.hipFile.path()
        nameAssets = scenepath.split("/Assets/")[1].split("/")[1]
        self.compOUT.setName(nameAssets, unique_name=True)
        
        self.find_variant(withVar)
        compoGeo = self.create_variant()
        if len(self.list_variant) != 1:
            compoGeo.bypass(False)
            self.make_separate_variant()
        else:
            compoGeo.bypass(True)
            self.bypass_connection()
    
    def create_variant(self):
        ref = self.refDupi
        tmp_ref = ref.parent()
        
        matRef = ref.outputs()[0]
        tmp_ref = matRef.parent()
        
        compoGeo = matRef.outputs()[0]
        

        for i, var in enumerate(self.list_variant):
            if i !=0:
                ref = ref.copyTo(tmp_ref)
                pos = ref.position()
                ref.setPosition([pos[0] + self.pasDecal, pos[1]])
                
                
                matRef = matRef.copyTo(tmp_ref)
                pos = matRef.position()
                matRef.setPosition([pos[0] + self.pasDecal, pos[1]])
                matRef.setInput(0, ref)
                compoGeo.setInput(i, matRef)
                
               
            lopimport = hou.node(f"stage/{ref}/sopnet/geo/modeling")
            lopimport.parm("primpattern").set(str(var.GetPath()))
            ref.setName(var.GetName(), unique_name=True)
        
        return compoGeo

    def find_variant(self, withVar):
        self.list_variant.clear()
        nmb_var = 0
        
        lopimport = hou.node(f"stage/{self.refDupi}/sopnet/geo/modeling")
        lopimport.parm('loppath').set(self.importLOP.path())
        lop_node = hou.node(self.importLOP.path())
        
        stage = lop_node.stage()
        for prim in stage.Traverse():
            print(prim)
            if prim.GetPath().pathString.startswith("/geo/xform/"):
                if len(str(prim.GetPath()).split("/")) == 4:
                    print(" trouver  ", prim.GetPath())
                    self.list_variant.append(prim)
                    nmb_var += 1
            
            if str(prim.GetPath()) == "/geo":
                source = prim
        

        if nmb_var == 1 or withVar == 1:
            print("-------------- qu'un seul variant creer base: /geo")
            self.list_variant.clear()
            self.list_variant.append(source)

    def bypass_connection(self):
        configurePrim = self.compOUT.outputs()[0]

        self.mergeToRig.setInput(0, configurePrim)
        self.mergeToSusbtance.setInput(0, configurePrim)


    def make_separate_variant(self):
        where = hou.node("/stage")

        configurePrim = self.compOUT.outputs()[0]
        pos_ref = self.compOUT.position()
        decal = (len(self.list_variant) * self.pasDecal) + 5
        
        old_decalTRS = 0

        for i, var in enumerate(self.list_variant):
            setVar = where.createNode("setvariant")
            setVar.parm("variantset1").set("geo")
            setVar.parm("variantname1").set(var.GetName())
            setVar.setPosition([pos_ref[0] - decal + (self.pasDecal * i), pos_ref[1] - 10])
            setVar.setInput(0, configurePrim)
            
            confLayer = where.createNode("configurelayer")
            confLayer.parm("flattenop").set("stage")
            confLayer.setPosition([pos_ref[0] - decal + (self.pasDecal * i), pos_ref[1] - 11])
            confLayer.setInput(0, setVar)
            self.mergeToRig.setInput(i, confLayer)


            decalTRS = self.calcul_DecalTransform(var)
            if i != 0:
                trs = where.createNode("xform")
                trs.parm("tx").set(old_decalTRS + decalTRS + self.pasTrsDecal)
                trs.parm("primpattern").set(f"/{self.compOUT.name()}/geo/render/xform/*")
                trs.setPosition([pos_ref[0] - decal + (self.pasDecal * i) + 1, pos_ref[1] - 13])
                trs.setInput(0, confLayer)

                old_decalTRS += decalTRS + self.pasTrsDecal
                self.mergeToSusbtance.setInput(i, trs)
            else:
                old_decalTRS = decalTRS
                self.mergeToSusbtance.setInput(i, confLayer)

    def calcul_DecalTransform(self, var):
        if var.IsA(UsdGeom.Xform):
            boxMax = []
            boxMin = []
            for child in var.GetChildren():
                boundable = UsdGeom.Boundable(child)
                bound = UsdGeom.Boundable.ComputeExtentFromPlugins(boundable, Usd.TimeCode.Default())
                boxMax.append(abs(bound[0][0]))
                boxMin.append(abs(bound[1][0]))
            
            transform = max(boxMax) + max(boxMin)

        else:
            boundable = UsdGeom.Boundable(var)
            bound = UsdGeom.Boundable.ComputeExtentFromPlugins(boundable, Usd.TimeCode.Default())
            transform = abs(bound[0][0]) + abs(bound[1][0])

        return transform
