import pymel.core as pm
import utils_pymel as utils
import secrets
import re
import os


def build_shader_operator(aiStandIn, sel):
    # Get the selected objects
    ai_merge = pm.createNode("aiMerge", n="aiMerge_%s" % aiStandIn.getParent().name())
    empty_displace = None
    shaders_used = []
    pm.addAttr(ai_merge, ln="mtoa_constant_is_target", attributeType="bool", defaultValue=True)
    pm.connectAttr(ai_merge + ".out", aiStandIn + ".operators[0]")
    meshes = pm.listRelatives(sel, allDescendents=True, shapes=True)
    for m in meshes:
        if "ShapeOrig" in m.name():
            meshes.remove(m)

    counter = 0
    for m in meshes:
        selection = m
        namespace = selection.namespace()
        selection = selection.longName()
        selection = selection.replace(namespace, "")
        selection = selection.replace("|", "/")
        # selection = selection + "*"

        sgs = m.outputs(type='shadingEngine')
        sgs = list(set(sgs))
        set_shader = pm.createNode("aiSetParameter", n="setShader_" + m)
        selection_attr = set_shader.attr("selection")
        selection_attr.set(selection)
        pm.connectAttr(set_shader + ".out", ai_merge + ".inputs[%s]" % (counter), f=True)
        counter += 1

        shader = ""
        displacement_shader_string = ""
        all_disp = None
        shader_maya_disp = None
        autoBump = False
        if len(sgs) == 1:
            sg = sgs[0]
            if sg.aiSurfaceShader.isConnected():
                shader_maya = sg.aiSurfaceShader.inputs()[0]
                shader += "'%s'" % shader_maya
                shaders_used.append(shader_maya)
            elif sg.surfaceShader.isConnected():
                shader_maya = sg.surfaceShader.inputs()[0]
                shader += "'%s'" % shader_maya
                shaders_used.append(shader_maya)

            if sg.displacementShader.isConnected():
                shader_maya_disp = sg.displacementShader.inputs()[0]
                displacement_shader_string = "'%s'" % shader_maya_disp
                shaders_used.append(shader_maya_disp)
        else:
            all_disp = [sg.displacementShader for sg in sgs if sg.displacementShader.isConnected()]
            for sg in sgs:
                if sg.aiSurfaceShader.isConnected():
                    shader_maya = sg.aiSurfaceShader.inputs()[0]
                    shaders_used.append(shader_maya)
                    shader += "'%s' " % (shader_maya)
                elif sg.surfaceShader.isConnected():
                    shader_maya = sg.surfaceShader.inputs()[0]
                    shaders_used.append(shader_maya)
                    shader += "'%s' " % (sg.surfaceShader.inputs()[0])
                # Check if there is any displacement shader because if there is one, all sg will need a displacement
                # So if an object has two shaders one with a displace and one without, we will need to create an empty shaders
                # to make the operator per face assignement work
                if len(all_disp) > 0:
                    if sg.displacementShader.isConnected():
                        shader_maya = sg.displacementShader.inputs()[0]
                        shaders_used.append(shader_maya)
                        displacement_shader_string += "'%s' " % (sg.displacementShader.inputs()[0])
                    else:
                        if not empty_displace:
                            empty_displace = pm.shadingNode("displacementShader", asShader=True)
                        autobump_attr = empty_displace.attr("aiDisplacementAutoBump")
                        autobump_attr.set(0)
                        pm.connectAttr(empty_displace.displacement, sg.displacementShader)
                        shaders_used.append(empty_displace)
                        displacement_shader_string += "'%s' " % (empty_displace)

        pm.setAttr(set_shader + ".assignment[0]", "shader=%s" % (shader), type="string")
        if displacement_shader_string != "":
            pm.setAttr(set_shader + ".assignment[1]", "disp_map=%s" % (displacement_shader_string), type="string")
            if all_disp:
                all_disp[0].inputs()[0].aiDisplacementAutoBump.get()

            else:
                if shader_maya_disp.aiDisplacementAutoBump.get() == True:
                    autoBump = True
            if autoBump:
                pm.setAttr(set_shader + ".assignment[2]", "bool disp_autobump=True", type="string")

        # CATCLARK
        sss_setName = m.ai_sss_setname.get()
        castsShadows = m.castsShadows.get()
        catclark_type = m.aiSubdivType.get()
        catclark_subdiv = m.aiSubdivIterations.get()
        if catclark_type > 0 and catclark_subdiv > 0:
            pm.setAttr(set_shader + ".assignment[3]", "subdiv_type='catclark'", type="string")
            pm.setAttr(set_shader + ".assignment[4]", "subdiv_iterations=%s" % (catclark_subdiv), type="string")
        if sss_setName != "":
            print(m.name() + " sss_setName" + sss_setName)
            pm.setAttr(set_shader + ".assignment[5]", "ai_sss_setname=%s" % (sss_setName), type="string")
        if castsShadows == 0:
            print("CAST SHADOW 0")
            pm.setAttr(set_shader + ".assignment[6]", "visibility=253", type="string")

    return shaders_used


def guess_dir():
    """Guess the asset directory and name from the current scene name.

    Returns:
        Tuple[str, str]: A tuple containing the asset directory and asset name,
    """
    scene = pm.system.sceneName()
    split = scene.split("/")
    split[0] = split[0] + "\\"  # idk why i need that, but otherwise the result is missing a "\" ex: D:proA\assset"
    for i, s in enumerate(reversed(split)):
        if s == "assets":
            print(os.path.dirname(os.path.join(*split)), split[-i])
            # asset_dir = os.path.join(*split[0:-(i - 1)])
            asset_dir = os.path.dirname(os.path.join(*split))
            asset_name = split[-i]
            return asset_dir, asset_name
    print("Dir not found in guess_dir")
    raise


def abcExport(sel):
    if not sel:
        pm.error("No selection")
    asset_dir, asset_name = guess_dir()
    abc_dir = os.path.join(asset_dir, "abc")
    # random_string = secrets.token_hex(5)
    abc_name = asset_name + "_mod.abc"
    abc_path = os.path.join(abc_dir, abc_name)
    abc_path = abc_path.replace("\\", "/")

    os.makedirs(abc_dir, exist_ok=True)
    job = '-frameRange 1 1 -stripNamespaces -uvWrite -worldSpace -writeFaceSets -writeVisibility -dataFormat ogawa -root %s -file "%s"' % (
    sel.longName(), abc_path)

    pm.AbcExport(j=job)
    return abc_path, abc_name


def create_standIn(abc_path, abc_name):
    aiStandIn = pm.createNode("aiStandIn", n=abc_name.split(".")[0] + "Shape")
    parent = aiStandIn.getParent()
    pm.rename(parent, abc_name.split(".")[0])
    aiStandIn.dso.set(abc_path)
    return aiStandIn


def export_arnold_graph(aiStandIn, shaders_used):
    asset_dir, asset_name = guess_dir()
    look_dir = os.path.join(asset_dir, "publish")
    path = os.path.join(look_dir, asset_name + "_operator.VOo1.ass")
    print(path)
    look = pm.listConnections(aiStandIn + ".operators")
    export_list = look + shaders_used
    pm.other.arnoldExportAss(export_list, f=path, s=True, asciiAss=True, mask=4112, lightLinks=0, shadowLinks=0,
                             fullPath=0)


def run():
    sel = pm.ls(sl=True)[0]
    utils.convert_selected_to_tx(sel)
    abc_path, abc_name = abcExport(sel)
    aiStandIn = create_standIn(abc_path, abc_name)
    shaders_used = build_shader_operator(aiStandIn, sel)
    export_arnold_graph(aiStandIn, shaders_used)
