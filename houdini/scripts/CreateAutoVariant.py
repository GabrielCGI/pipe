from pxr import Usd, UsdGeom
import socket
import hou
import sys





class autoVariant():
    def __init__(self, sel=None, ui=True):
        self.statue = {"statue": True, "mesage": ""}
        if not sel: 
            sel = hou.selectedNodes()
        if len(sel) != 3:
            if ui:
                hou.ui.displayMessage("Select 3 nodes in this order: Prism LOP import / componentIN / componentOUT", buttons=("OK",) ,severity=hou.severityType.Error)
            self.statue = {"statue": False, "mesage": "Select 3 nodes in this order: Prism LOP import / componentIN / componentOUT"}
            return

        self.importLOP = sel[0]
        self.refDupi = sel[1]
        self.compOUT = sel[2]

        self.list_variantPath = {}
        self.pasDecal = 2
        self.pasTrsDecal = 1
        self.mergeToRig = hou.node("/stage/merge4")
        self.mergeToSusbtance = hou.node("/stage/merge5")


        scenepath = hou.hipFile.path()
        if not scenepath:
            if ui:
                hou.ui.displayMessage("the scene is not save please save your scene in the good assets folder", buttons=("OK",) ,severity=hou.severityType.ImportantMessage)
            self.statue = {"statue": False, "mesage": "the scene is not save please save your scene in the good assets folder"}
            return
        
        try:
            nameAssets = scenepath.split("/Assets/")[1].split("/")[1]
        except:
            if ui:
                hou.ui.displayMessage("To use the tool, you must be in the lookdev scene of the asset", buttons=("OK",) ,severity=hou.severityType.ImportantMessage)
            self.statue = {"statue": False, "mesage": "To use the tool, you must be in the lookdev scene of the asset"}
            return
        


        if ui:
            withVar = hou.ui.displayMessage("it's variant ?", buttons=("Yes", "No", "skip") , close_choice=2)
        else:
            withVar = 1
        
        if withVar == 2:
            return
        
    
        self.compOUT.setName(nameAssets, unique_name=True)
        
        list_variant = self.find_variant(withVar, nameAssets)
        compoGeo = self.create_variant(list_variant.copy(), withVar)
        if len(list_variant) != 1:
            compoGeo.bypass(False)
            if self.mergeToRig is not None and self.mergeToRig is not None: 
                self.make_separate_variant(list_variant, withVar)
        else:
            compoGeo.bypass(True)
            self.bypass_connection()
    
    def create_variant(self, list_variant, withVar):
        ref = self.refDupi
        tmp_ref = ref.parent()
        listMatRef = []
        modif = False
        Dref = ref
        
        if not withVar:
            stage = hou.node('/stage')
            allChild = stage.children()
            for node in allChild:
                if node.type().name() == "componentgeometry":
                    try:
                        lopimport = hou.node(f"stage/{node}/sopnet/geo/modeling")
                        var = lopimport.parm("primpattern").eval()
                        if var in self.list_variantPath.keys():
                            modif = True
                            list_variant.remove(self.list_variantPath[var][0])
                    except Exception as e:
                        print(e)
        
        for i in range(3):
            Dref = Dref.outputs()[0]
            listMatRef.append(Dref)
            if Dref.type().name() == "componentmaterial":
                break
        
        compoGeo = listMatRef[-1].outputs()[0]
        nmbStart = len(compoGeo.inputs())
        
        for i, var in enumerate(list_variant):
            if i !=0 or nmbStart != 1 or modif:
                add = 1 if nmbStart !=1 else 0
                ref = ref.copyTo(tmp_ref)
                pos = ref.position()
                ref.setPosition([pos[0] + self.pasDecal, pos[1]])
                toCon = ref
                
                for matRef in listMatRef:
                    NmatRef = matRef.copyTo(tmp_ref)
                    pos = NmatRef.position()
                    if modif and nmbStart ==1:
                        add += 1
                    NmatRef.setPosition([pos[0] + self.pasDecal*(i + add), pos[1]])
                    NmatRef.setInput(0, toCon)
                    toCon = NmatRef
                    compoGeo.setInput(i + nmbStart, NmatRef)
                
               
            lopimport = hou.node(f"stage/{ref}/sopnet/geo/modeling")
            lopimport.parm("primpattern").set(str(var.GetPath()))
            ref.setName(var.GetName(), unique_name=True)
        
        return compoGeo

    def find_variant(self, withVar, nameAssets):
        list_variant =[]
        old_decalTRS = 0
        nmb_var = 0
        
        lopimport = hou.node(f"stage/{self.refDupi}/sopnet/geo/modeling")
        lopimport.parm('loppath').set(self.importLOP.path())
        lop_node = hou.node(self.importLOP.path())
        
        stage = lop_node.stage()
        search_path = "/geo/xform/"
        path_source = "/geo"
        incre = 4
        for prim in stage.Traverse():
            if not prim.GetPath().pathString.startswith(path_source):
                search_path = f"/{nameAssets}/geo/render/xform"
                path_source = "/" + nameAssets + "/geo"
                incre = 6
            
            if prim.GetPath().pathString.startswith(search_path):
                if len(str(prim.GetPath()).split("/")) == incre:
                    print(" trouver  ", prim.GetPath())
                    list_variant.append(prim)
                    transform = self.calcul_DecalTransform(prim)
                    if nmb_var == 0:
                        transform = 0
                    self.list_variantPath[str(prim.GetPath())] = [prim, old_decalTRS + transform + self.pasTrsDecal]
                    old_decalTRS += transform + self.pasTrsDecal
                    nmb_var += 1
            
            if str(prim.GetPath()) == path_source:
                source = prim

        if nmb_var == 1 or withVar == 1:
            print("-------------- qu'un seul variant creer base: /geo")
            list_variant.clear()
            list_variant.append(source)
        
        return list_variant

    def bypass_connection(self):
        configurePrim = self.compOUT.outputs()[0]

        self.mergeToRig.setInput(0, configurePrim)
        self.mergeToSusbtance.setInput(0, configurePrim)

    def make_separate_variant(self, list_variant, withVar):
        where = hou.node("/stage")
        modif = False

        enterMergeToRig = self.mergeToRig.inputs()
        configurePrim = self.compOUT.outputs()[0]
        pos_ref = self.compOUT.position()
        nmbInput = 0
        if enterMergeToRig:
            if enterMergeToRig[0] != configurePrim:
                nmbInput = len(self.mergeToRig.inputs())
            
        
        for node in configurePrim.outputs():
            if node.type().name() == "setvariant":
                try:
                    path = "/geo/xform/" + str(node.parm("variantname1").eval())
                    if path in self.list_variantPath.keys():
                        modif = True
                        list_variant.remove(self.list_variantPath[path][0])
                except Exception as e:
                    print(e)


        decal = (1+ len(list_variant) * self.pasDecal) + 5

        for i, var in enumerate(list_variant):
            setVar = where.createNode("setvariant")
            setVar.parm("variantset1").set("geo")
            setVar.parm("variantname1").set(var.GetName())
            setVar.setPosition([pos_ref[0] - decal + (self.pasDecal * (i + nmbInput)), pos_ref[1] - 10])
            setVar.setInput(0, configurePrim)
            
            confLayer = where.createNode("configurelayer")
            confLayer.parm("flattenop").set("stage")
            confLayer.setPosition([pos_ref[0] - decal + (self.pasDecal * (i + nmbInput)), pos_ref[1] - 11])
            confLayer.setInput(0, setVar)
            self.mergeToRig.setInput(i + nmbInput, confLayer)

            if i != 0 or modif:
                trs = where.createNode("xform")
                trs.parm("tx").set(self.list_variantPath[str(var.GetPath())][1])
                trs.parm("primpattern").set(f"/{self.compOUT.name()}/geo/render/xform/*")
                trs.setPosition([pos_ref[0] - decal + (self.pasDecal * (i + nmbInput)) + 1, pos_ref[1] - 13])
                trs.setInput(0, confLayer)

                self.mergeToSusbtance.setInput(i + nmbInput, trs)
            else:
                self.mergeToSusbtance.setInput(i + nmbInput, confLayer)

    def calcul_DecalTransform(self, var):
        if var.IsA(UsdGeom.Xform):
            totalSize = 0.0
            for child in var.GetChildren():
                if child.IsA(UsdGeom.Xform):
                    totalSize = max(totalSize, self.calcul_DecalTransform(child))
                else:
                    boundable = UsdGeom.Boundable(child)
                    bound = UsdGeom.Boundable.ComputeExtentFromPlugins(boundable, Usd.TimeCode.Default())
                    size_x = (bound[1][0] - bound[0][0]) * 1.2
                    totalSize = max(totalSize, size_x)

            transform = totalSize

        else:
            boundable = UsdGeom.Boundable(var)
            bound = UsdGeom.Boundable.ComputeExtentFromPlugins(boundable, Usd.TimeCode.Default())
            transform = (bound[1][0] - bound[0][0]) * 1.2

        return transform
