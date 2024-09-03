
#! python3

import os
import rhinoscriptsyntax as rs
import scriptcontext as sc
import math

import System
import System.Collections.Generic
import Rhino


# Set the input folder containing .3dm files
input_folder = r'C:\Users\j.monti\Documents\julia\swaChristmas\3Ddata'

# Set the output folder where OBJ files will be saved
output_folder = r'C:\Users\j.monti\Documents\julia\swaChristmas\3Ddata_out'

selected_preset = "high"  # Change this to the desired preset: "low", "high", or "ultrahigh"

# Define common settings
common_settings = (
    "_Geometry=_Mesh "
    "_EndOfLine=CRLF "
    "_ExportRhinoObjectNames=2 "
    "_ExportGroupNameLayerNames=1"
    "_ExportMeshTextureCoordinates=_Yes "
    "_ExportMeshVertexNormals=_Yes "
    "_CreateNGons=_No "
    "_ExportMaterialDefinitions=_Yes "
    "_YUp=_Yes "
    "_WrapLongLines=Yes "
    "_VertexWelding=_Welded "
    "_WritePrecision=17 "
    "_Enter "
    "_DetailedOptions "
    "_JaggedSeams=_No "
    "_PackTextures=_No "
    "_Refine=_Yes "
    "_SimplePlane=_No "
)

# Define quality presets
presets = {
    "low": (
        common_settings +
        "_AdvancedOptions "
        "_Angle=20 "
        "_AspectRatio=0 "
        "_Distance=0.0 "
        "_Density=0 "
        "_Grid=0 "
        "_MaxEdgeLength=0 "
        "_MinEdgeLength=0.0001 "
        "_Enter _Enter"
    ),
    "high": (
        common_settings +
        "_AdvancedOptions "
        "_Angle=20 "
        "_AspectRatio=0 "
        "_Distance=0.0 "
        "_Density=1 "
        "_Grid=0 "
        "_MaxEdgeLength=0.2 "
        "_MinEdgeLength=0.0001 "
        "_Enter _Enter"
    ),
}

# Function to export .3dm to OBJ with specified options
def export_to_obj(file_path, settings):
    rs.EnableRedraw(False)
    rs.DocumentModified(False)
    rs.Command("_-Open \"" + file_path + "\" _NoSave _Enter")

    # Scale all objects from the world center by 0.1 to convert from mm to cm
    scale_factor = 0.1
    rs.ScaleObjects(rs.AllObjects(), [0, 0, 0], [scale_factor, scale_factor, scale_factor], copy=False)

    rs.UnselectAllObjects()
    all_objects = rs.AllObjects()
    if all_objects:
        rs.SelectObjects(all_objects)
    name = os.path.splitext(os.path.basename(file_path))[0]
    settings_str = settings
    command = f'-_Export "{output_folder}/{name}_{selected_preset}.obj" {settings_str} _Enter'
    rs.Command(command, True)
    rs.EnableRedraw(True)

# List all .3dm files in the input folder
input_files = [f for f in os.listdir(input_folder) if f.endswith(".stp")]

# Loop through each .3dm file and export to OBJ using the selected quality preset


for input_file in input_files:
    # Create the full path for the input .3dm file
    input_path = os.path.join(input_folder, input_file)

    # Export the opened file to OBJ format with the selected preset
    export_to_obj(input_path, presets[selected_preset])

    print(f"Exported {input_file} to OBJ with {selected_preset} preset")