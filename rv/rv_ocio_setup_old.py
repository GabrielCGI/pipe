# sample rv_ocio_setup.py guided by autodesk support

import os
from rv import commands
import PyOpenColorIO as OCIO
import pathlib

def ocio_config_from_media(media, attributes):

    #
    #  Set OCIO environment variable with the config path
  
    config_path = r"R:/pipeline/networkInstall/OpenColorIO-Configs/PRISM/illogic_V01-cg-config-v1.0.0_aces-v1.3_ocio-v2.1.ocio"
    os.environ["OCIO"] = config_path
    print ("ocio loaded from " + config_path )

    return OCIO.Config.CreateFromFile(config_path)

def ocio_node_from_media(config, node, default, media=None, attributes={}):

    #
    #  Based on the incoming node assemble the corresponding pipeline
    #

    result = [{"nodeType" : d, "context" : {}, "properties" : {}} for d in default]
    context = {}

    # Resolve the scene_linear role to the actual color space name
    # OCIO.ROLE_SCENE_LINEAR is just a role key - we need the actual color space name
    try:
        scene_linear_colorspace = config.getCanonicalName(OCIO.ROLE_SCENE_LINEAR)
    except:
        # Fallback to a known linear color space if role doesn't exist
        scene_linear_colorspace = "ACES - ACEScg"

    EXR_LINEAR_FILE_COLOURSPACE = "ACES - ACEScg"
    QT_COLOURSPACE = "sRGB - Display"
    JPG_COLOURSPACE  = "sRGB - Display"
    DISPLAY = "sRGB - Display"
    VIEW = "ACES 1.0 - SDR Video"

    if media:
        file_extension=pathlib.Path(media).suffix
        print("ext: %s" % file_extension)

        # if extension is .exr
        if file_extension == ".exr":
            sourceColorSpace = EXR_LINEAR_FILE_COLOURSPACE
            display = DISPLAY
            view = VIEW
        # if extension is .mov
        elif file_extension == ".mov" or file_extension == ".mp4":
            sourceColorSpace = QT_COLOURSPACE
            display = DISPLAY
            view = VIEW
        elif file_extension == ".jpg" or file_extension == ".png":
            sourceColorSpace = JPG_COLOURSPACE
            display = DISPLAY
            view = VIEW
        # if extension isn't .exr or .mov, 
        # set a default value for sourceColorSpace, display and view
        else:
            sourceColorSpace = EXR_LINEAR_FILE_COLOURSPACE
            display = DISPLAY
            view = VIEW
        print("color: %s" % sourceColorSpace)
        print("display: %s" % display)
        print("view: %s" % view)
    else:
        display = DISPLAY
        view = VIEW

    nodeType = commands.nodeType(node)
    if (nodeType == "RVLinearizePipelineGroup"):
        result = [
            {"nodeType": "OCIOFile",
             "context" : context,
             "properties" : {
                 "ocio.function"            : "color",
                 "ocio.inColorSpace"        : sourceColorSpace,
                 "ocio_color.outColorSpace" : scene_linear_colorspace}},
            {"nodeType" : "RVLensWarp", "context" : {}, "properties" : {}}]
    elif (nodeType == "RVDisplayPipelineGroup"):
        result = [
            {
                "nodeType": "OCIODisplay",
                 "context": context,
                 "properties": {
                     "ocio.function"        : "display",
                     "ocio.inColorSpace"    : scene_linear_colorspace,
                     "ocio_display.view"    : view,
                     "ocio_display.display" : display }}]

    return result