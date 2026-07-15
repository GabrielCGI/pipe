import os
import re


def output_srgb_to_aces(input_path):
    try:
        input_file = None
        range_0 = None
        range_1 = None
        # If input_path is dir so it is a sequence
        if os.path.isdir(input_path):
            # Retrieve the sequence and the range of frames
            for child_name in os.listdir(input_path):
                path = os.path.join(input_path, child_name)
                match = re.match(r"^(.+[\\\/][\w\.]*)([0-9]{4})(\.\w+)$", path)
                if not match:
                    continue
                if input_file is None:
                    input_file = (match.group(1) + "####" + match.group(3)).replace("\\", "/")
                frame = int(match.group(2))
                if range_0 is None or range_0 > frame: range_0 = frame
                if range_1 is None or range_1 < frame: range_1 = frame
            # Test if a sequence has been found
            if input_file is None:
                print("Give a folder with a sequence")
                os.system("pause")
                return
        # If input_path is a file so it is a single file
        elif os.path.exists(input_path):
            input_file = input_path
            range_0 = 1
            range_1 = 1
        else:
            print("Give a file or a folder of a sequence")
            os.system("pause")
            return
        input_dirname, input_basename = os.path.split(input_file)
        input_basename_without_ext = ".".join(input_basename.split(".")[:-1])
        output_file = os.path.join(input_dirname, "output_srgb", input_basename_without_ext+".exr").replace("\\", "/")
        # Create Reader
        reader = app.createReader(input_file)
        # Change Input Colorspace to sRGB (index 105)
        colorSpaceOut = reader.getParam("ocioInputSpaceIndex")
        colorSpaceOut.setValue(105)
        # Change Output Colorspace to ACES (index 4)
        colorSpaceOut = reader.getParam("ocioOutputSpaceIndex")
        colorSpaceOut.setValue(4)
        # Create Writer
        writer = app.createWriter(output_file)
        # Change format_type
        formatType = writer.getParam("formatType")
        formatType.setValue(0)
        # Connect the writer to the reader
        writer.connectInput(0, reader)
        # Render
        app.render(writer, range_0, range_1)
    except Exception as e:
        print(str(e))
        os.system("pause")

output_srgb_to_aces(input_path)
