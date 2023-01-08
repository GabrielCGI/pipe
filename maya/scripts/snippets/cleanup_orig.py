import pymel.core as pm

def cleanup_intermediate_objects():

    unused_intermediate_objects = []
    all_meshes = pm.ls(type='mesh')
    for node in all_meshes:
        if len(node.inputs()) == 0 \
           and len(node.outputs()) == 0 \
           and node.intermediateObject.get() \
           and node.referenceFile() is None:
            unused_intermediate_objects.append(node)
    pm.delete(unused_intermediate_objects)
cleanup_intermediate_objects()