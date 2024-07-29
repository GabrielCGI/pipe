import hou


def paste_parms(source,target):
    nummaterial_parm = source.parm('nummaterials')
    count = nummaterial_parm.valueAsData()
    for i in range(1,count+1):

        primpattern_str= f"primpattern{i}"
        primpattern = source.parm(primpattern_str)
        target_primpattern = target.parm(primpattern_str)
        target_primpattern.set(primpattern)
        print("Succes")
        print (target_primpattern.valueAsData())

def component_material_parsing():
    # Iterate over all selected nodes
    selected = hou.selectedNodes()
    source = selected[0]
    targets = selected[1:]
    for target in targets:
        paste_parms(source, target)


component_material_parsing()
