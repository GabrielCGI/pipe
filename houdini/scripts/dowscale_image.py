import os
import subprocess

# Path to the Houdini tool
hoiiotool_path = r"C:\Program Files\Side Effects Software\Houdini 20.5.320\bin\hoiiotool.exe"

# Folder containing textures
textures_folder = r"D:\toto\ZDISP"

# Subfolder for resized textures
output_folder = os.path.join(textures_folder, "2k")

# Resize parameter
resize_param = "2048x0"

# Function to batch convert textures
def batch_convert_textures(tool_path, folder, output_folder, resize):
    # Check if the folder exists
    if not os.path.exists(folder):
        print(f"Folder {folder} does not exist.")
        return

    # Create the output folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # List all files in the folder
    files = os.listdir(folder)

    # Process each file
    for file in files:
        file_path = os.path.join(folder, file)
        if os.path.isfile(file_path):
            # Create output file path with .exr extension
            file_name, _ = os.path.splitext(file)
            output_file_path = os.path.join(output_folder, f"{file_name}.exr")
            
            # Construct the command
            command = [tool_path, file_path, "-resize", resize, "-o", output_file_path]
            
            # Execute the command
            try:
                result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"Successfully processed {file_path} -> {output_file_path}")
            except subprocess.CalledProcessError as e:
                print(f"Error processing {file_path}: {e.stderr.decode()}")

# Run the batch conversion
batch_convert_textures(hoiiotool_path, textures_folder, output_folder, resize_param)
