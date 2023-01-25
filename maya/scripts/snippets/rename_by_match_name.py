source =pm.ls(sl=True)[0]
target = pm.ls(sl=True)[1]

msh_source = source.getChildren()
msh_target = target.getChildren()

for m in msh_target:
    match = "rose:"+m.name()
    if match in msh_source:
        shapeName =msh_source[msh_source.index(match)].getShape()
        cleanName = shapeName.split(":")[-1].split("Shape")[0]
        print (cleanName)
        
        pm.rename(m, cleanName)
