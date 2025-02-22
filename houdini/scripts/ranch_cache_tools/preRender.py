# This script will be executed before the execution of an render state in the Prism State Manager.
# You can use this file to define project specific actions, like cleaning up your scene or preparing your scene for rendering.

# Example:
# print "Prism is going to render now."

# If the main function exists in this script, it will be called.
# The "kwargs" argument is a dictionary with usefull information about Prism and the current export.

# def main(*args, **kwargs):
#     print(args)
#     print(kwargs)
#     print(kwargs["core"].projectName)
#     print(kwargs["state"].l_taskName.text())
#     print(kwargs["scenefile"])
#     print(kwargs["settings"])



KARMA_RENDER_SETTING_TYPE = 'karmarenderproperties'
DWA_B = 'zips'
EXR_COMPRESSION_TYPE = 'image_exr_compression'
try:
    import hou
    import loputils
except:
    print("Skipping import hou...")

def set_parm_expression_to_python(parm):
    print("DEBUG: postrender parm =", parm)
    if not parm:
        print("DEBUG: No 'postrender' parameter found; nothing to do.")
        return

    # Check for keyframes or expression
    keyframes = parm.keyframes()

    # Only do the conversion if exactly one keyframe is found
    if len(keyframes) == 0:
        # If 0 keyframes, forcibly create a Python expression
        current_value = parm.evalAsString()
        print(f"DEBUG: Set postrender parm expression to python")
        parm.setExpression(current_value, language=hou.exprLanguage.Python)
    else: 
        print(f"DEBUG: Parm postrender already a Python expression")       

def set_output_processors_search_path(kwargs):
  

    node = hou.node(kwargs["state"].node.path())
    print("DEBUG: Root node =", node)

    # Check if the node is locked, unlock if necessary
    if node and node.isLockedHDA():
        node.allowEditingOfContents(True)
        print("DEBUG: Unlocked HDA for editing.")


    if not node:
        print("Error: Fail to get node Lop Render to update... The ouputprocessor SEARCH_PATH will not be added")

    usd_rop_node = node.node("usd_rop")
    usdrender_rop_node = node.node("usdrender_rop1")


    if not usd_rop_node or not usdrender_rop_node:
        print("DEBUG: No usd_rop node or usdrender_rop_node found; early return.")
        return

    # --- Existing Logic to set "outputprocessors" parameter ---
    print("\n Debug: ------ Output processors processing -------- ")
    parm = usd_rop_node.parm("outputprocessors")
    print("DEBUG: outputprocessors parm =", parm)
    if parm:
        try:
            print("DEBUG: Setting outputprocessors to 'usesearchpaths'")
            parm.set("usesearchpaths")
            
            processor_kwargs = {
                "node": usd_rop_node,
                "parm": parm,
                "script_value": "usesearchpaths",
                "script_multiparm_index": 0
            }
            loputils.handleOutputProcessorAdd(processor_kwargs)
            print("DEBUG: handleOutputProcessorAdd success.")
        except hou.OperationFailed as e:
            print("DEBUG: Skip add output processor - Already exist:")

        search_path_parm = usd_rop_node.parm("usesearchpaths_searchpath")
        if search_path_parm:
            search_path_parm.set("i:/;r:/;I:/;R:/;")
            print("DEBUG: Set search path parm to i:/;r:/;I:/;R:/;")

        simple_relative_paths_parm = usd_rop_node.parm("enableoutputprocessor_simplerelativepaths")
        print("DEBUG: enableoutputprocessor_simplerelativepaths parm =", simple_relative_paths_parm)
        if simple_relative_paths_parm:
            simple_relative_paths_parm.set(0)
            print("DEBUG: Disabled simplerelativepaths processor.")

    # --- New Logic for "postrender" parameter ---
    print("\nDebug: ------ Python expression processing --------")
    usd_rop_postrender_parm = usd_rop_node.parm("postrender")
    usdrender_rop_postrender_parm = usdrender_rop_node.parm("postrender")
    set_parm_expression_to_python(usd_rop_postrender_parm)
    set_parm_expression_to_python(usdrender_rop_postrender_parm)


def changeEXRCompression(kwargs):
    """Change EXR compression to DWA-B in every karma render node.

    Args:
        kwargs (dict): preRender context.
    """    

    stage: hou.LopNetwork = kwargs["state"].node.parent()
    render_setting_list = []
    for node in stage.children():
        if node.type().name() == KARMA_RENDER_SETTING_TYPE:
            render_setting_list.append(node)
    
    for render_setting_node in render_setting_list:
        render_setting_node.parm(EXR_COMPRESSION_TYPE).set(DWA_B)


def main(*args, **kwargs):
    
    
    core = kwargs["core"]
    if core.appPlugin.pluginName == "Houdini":
        # Only proceed if GUI is available
        if not hou.isUIAvailable():
            
            print("Houdini is not in GUI mode. Skipping processor & exr compression.")
            return
        else: 
            print("Houdini is GUI mode. Strating processor & exr compression in pre-render.")
            changeEXRCompression(kwargs)
            set_output_processors_search_path(kwargs)
            hou.hipFile.save()
