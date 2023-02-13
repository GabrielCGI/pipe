import pymel.core as pm

selection = pm.ls(sl=True)

if len(selection) >= 2:
    meshes_source = pm.listRelatives(selection[0], allDescendents=True, type="mesh")
    meshes_target = pm.listRelatives(selection[1], allDescendents=True, type="mesh")

    for mesh_s in meshes_source:
        if "ShapeOrig" not in mesh_s.name():
            mesh_s_name = mesh_s.name(long=None)
            for mesh_t in meshes_target:
                mesh_t_name = mesh_t.name(long=None)
                if mesh_s_name == mesh_t_name:
                    pm.select(mesh_s, r=True)
                    pm.select(mesh_t, tgl=True)
                    pm.transferShadingSets(sampleSpace=0, searchMethod=3)