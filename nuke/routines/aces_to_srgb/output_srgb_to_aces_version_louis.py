import os
import re

def digest_input_path(image_path):
    print("-------------------------------------digest_input_path IN------------------------------")
    """
    Processes the input path to determine if it is a single file or a sequence of images.

    Args:
        image_path (str): Path to the input file or folder containing the image sequence.

    Returns:
        tuple: (input_file, range_start, range_end)
            input_file (str): The template or file path for the input.
            range_start (int): Start frame of the sequence or 1 for a single file.
            range_end (int): End frame of the sequence or 1 for a single file.
    """



    # Process the directory to find sequences
    child_name_list=[]
    for child_name in os.listdir(image_path):
        path = os.path.join(image_path, child_name)
        child_name_list.append(path)

    for child_name in child_name_list:
        convert_srgb_to_aces(child_name)


def convert_srgb_to_aces(input_file):
    print("-------------------------------------convert IN------------------------------")
    print(f"convert {input_file}srgb_to_aces")
    """
    Converts input image(s) from sRGB to ACES color space.

    Args:
        input_file (str): Template or file path for the input.
        range_start (int): Start frame of the sequence or 1 for a single file.
        range_end (int): End frame of the sequence or 1 for a single file.
    """
    try:
        # Prepare the output path
        input_dirname, input_basename = os.path.split(input_file)
        input_basename_without_ext = ".".join(input_basename.split(".")[:-1])
        output_file = os.path.join(input_dirname, "output_srgb", f"{input_basename_without_ext}.exr").replace("\\", "/")

        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Create the reader for the input file or sequence
        reader = app.createReader(input_file)

        # Set the input color space to sRGB (index 105 in the application)
        reader.getParam("ocioInputSpaceIndex").setValue(105)

        # Set the output color space to ACES (index 4 in the application)
        reader.getParam("ocioOutputSpaceIndex").setValue(4)

        # Create the writer for the output file
        writer = app.createWriter(output_file)

        # Set the output format type (0 indicates default EXR format)
        writer.getParam("formatType").setValue(0)
        writer.getParam("firstFrame").setValue(1)  # Render frame 1
        writer.getParam("lastFrame").setValue(1)

        # Connect the writer to the reader
        writer.connectInput(0, reader)

        # Render the output for the specified frame range
        print(f"render {input_file}srgb_to_aces")
        app.render(writer, 1, 1)
        print(f"rendering done? {input_file}srgb_to_aces")

        print(f"Conversion completed. Output saved to: {output_file}")

    except Exception as e:
        print(f"Error during processing: {str(e)}")
    print("-------------------------------------digest_input_path OUT------------------------------")
# Example usage
# Replace 'input_path' with the actual path to your file or sequence


digest_input_path(input_path)