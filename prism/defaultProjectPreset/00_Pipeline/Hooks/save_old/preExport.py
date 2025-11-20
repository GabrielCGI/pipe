
# def main(*args, **kwargs):
#     print(args)
#     print(kwargs)
#     print(kwargs["core"].projectName)
#     print(kwargs["state"].l_taskName.text())
#     print(kwargs["scenefile"])
#     print(kwargs["startframe"])
#     print(kwargs["endframe"])
#     print(kwargs["outputpath"])


RANCH_EXPORTER_PATH = "R:/pipeline/pipe/prism/ranch_cache_scripts"
import sys
sys.path.append(RANCH_EXPORTER_PATH)

# TO enable print again set DEBUG to True
DEBUG = False
def pdebug(msg):
    if DEBUG:
        print(msg)

try:
    import hou
    import loputils
except:
    pass

def set_output_processors_search_path(kwargs):
    node = hou.node(kwargs["state"].node.path())
    pdebug(f"DEBUG: Root node = {node}")

    # Check if the node is locked, unlock if necessary
    if node and node.isLockedHDA():
        node.allowEditingOfContents(True)
        pdebug("DEBUG: Unlocked HDA for editing.")


    if not node:
        pdebug("Error: Fail to get node Lop Render to update... The ouputprocessor SEARCH_PATH will not be added")

    usd_rop_node = node.node("usd_rop1")
    # usdrender_rop_node = node.node("usdrender_rop1")


    if not usd_rop_node: # or not usdrender_rop_node:
        pdebug("DEBUG: No usd_rop node or usdrender_rop_node found; early return.")
        return

    # --- Existing Logic to set "outputprocessors" parameter ---
    pdebug("\nDEBUG: ------ Output processors processing -------- ")
    parm = usd_rop_node.parm("outputprocessors")
    pdebug(f"DEBUG: outputprocessors parm = {parm}")
    if parm:
        try:
            pdebug("DEBUG: Setting outputprocessors to 'usesearchpaths'")
            parm.set("usesearchpaths")
            
            processor_kwargs = {
                "node": usd_rop_node,
                "parm": parm,
                "script_value": "usesearchpaths",
                "script_multiparm_index": 0
            }
            loputils.handleOutputProcessorAdd(processor_kwargs)
            pdebug("DEBUG: handleOutputProcessorAdd success.")
        except hou.OperationFailed as e:
            pdebug("DEBUG: Skip add output processor - Already exist:")

        search_path_parm = usd_rop_node.parm("usesearchpaths_searchpath")
        if search_path_parm:
            search_path_parm.set("i:/;r:/;I:/;R:/;")
            pdebug("DEBUG: Set search path parm to i:/;r:/;I:/;R:/;")

        simple_relative_paths_parm = usd_rop_node.parm("enableoutputprocessor_simplerelativepaths")
        pdebug(f"DEBUG: enableoutputprocessor_simplerelativepaths parm = {simple_relative_paths_parm}")
        if simple_relative_paths_parm:
            simple_relative_paths_parm.setExpression("0")
            pdebug("DEBUG: Disabled simplerelativepaths processor.")
   
    
def main(*args, **kwargs):
    
    core = kwargs["core"]
    scenefile = kwargs["scenefile"]
    
    if core.appPlugin.pluginName == 'Houdini':
        import ranchExporter
        if ranchExporter.is_light_cache(kwargs):
            set_output_processors_search_path(kwargs)
