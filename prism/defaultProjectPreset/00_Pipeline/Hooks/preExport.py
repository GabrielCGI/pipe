import logging
import sys



logger = logging.getLogger("IllogicPlugin."+__name__)
RANCH_EXPORTER_PATH = "R:/pipeline/pipe/prism/ranch_cache_scripts"
sys.path.append(RANCH_EXPORTER_PATH)


def set_output_processors_search_path(kwargs):
    import loputils #type: ignore
    import hou #type: ignore

    node = hou.node(kwargs["state"].node.path())
    logger.info(f"Root node = {node}")

    # Check if the node is locked, unlock if necessary
    if node and node.isLockedHDA():
        node.allowEditingOfContents(True)
        logger.info("Unlocked HDA for editing.")


    if not node:
        logger.error("Fail to get node Lop Render to update... The ouputprocessor SEARCH_PATH will not be added")

    usd_rop_node = node.node("usd_rop1")
    # usdrender_rop_node = node.node("usdrender_rop1")


    if not usd_rop_node: # or not usdrender_rop_node:
        logger.info("No usd_rop node or usdrender_rop_node found; early return.")
        return

    # --- Existing Logic to set "outputprocessors" parameter ---
    logger.info("\n------ Output processors processing -------- ")
    parm = usd_rop_node.parm("outputprocessors")
    logger.info(f"outputprocessors parm = {parm}")
    if parm:
        try:
            logger.info("Setting outputprocessors to 'usesearchpaths'")
            parm.set("usesearchpaths")
            
            processor_kwargs = {
                "node": usd_rop_node,
                "parm": parm,
                "script_value": "usesearchpaths",
                "script_multiparm_index": 0
            }
            loputils.handleOutputProcessorAdd(processor_kwargs)
            logger.info("handleOutputProcessorAdd success.")
        except hou.OperationFailed:
            logger.info("Skip add output processor - Already exist:")

        search_path_parm = usd_rop_node.parm("usesearchpaths_searchpath")
        if search_path_parm:
            search_path_parm.set("i:/;r:/;I:/;R:/;")
            logger.info("Set search path parm to i:/;r:/;I:/;R:/;")

        simple_relative_paths_parm = usd_rop_node.parm("enableoutputprocessor_simplerelativepaths")
        logger.info(f"enableoutputprocessor_simplerelativepaths parm = {simple_relative_paths_parm}")
        if simple_relative_paths_parm:
            simple_relative_paths_parm.setExpression("0")
            logger.info("Disabled simplerelativepaths processor.")
   
    
def main(*args, **kwargs):
    logger.info("START: file hook preExport")
    core = kwargs["core"]
    if core.appPlugin.pluginName == 'Houdini':
        import ranchExporter #type: ignore
        if ranchExporter.is_light_cache(kwargs):
            set_output_processors_search_path(kwargs)
    logger.info("END: file hook preExport")
