import os
import re


def aces_to_srgb(folder):
    try:
        # Test if folder
        if not os.path.isdir(folder):
            print("Give a folder")
            os.system("pause")
            return

        input_file = None
        range_0 = None
        range_1 = None

        # Retrieve the sequence and the range of frames
        for child_name in os.listdir(folder):
            if child_name.endswith(".exr") and len(child_name) >= 8 and child_name[-8:-4].isdigit():
                frame = int(child_name[-8:-4])

                if input_file is None:
                    input_file = os.path.join(folder, child_name[:-8] + "####.exr").replace("\\", "/")

                if range_0 is None or range_0 > frame:
                    range_0 = frame
                if range_1 is None or range_1 < frame:
                    range_1 = frame

        # Test if a sequence has been found
        if input_file is None:
            print("Give a folder with EXR")
            os.system("pause")
            return

        input_dirname, input_basename = os.path.split(input_file)
        output_file = os.path.join(input_dirname, "PNG", input_basename).replace("\\", "/").replace(".exr", ".png")

        # Create Reader
        reader = app.createReader(input_file)
        colorSpaceOut = reader.getParam("ocioInputSpaceIndex")
        colorSpaceOut.setValue(4)

        # Create Writer
        writer = app.createWriter(output_file)

        # Change Format Type
        formatType = writer.getParam("formatType")
        formatType.setValue(0)

        # Change Output Colorspace to sRGB index 105)
        colorSpaceOut = writer.getParam("ocioOutputSpaceIndex")
        colorSpaceOut.setValue(105)

        # Connect the writer to the reader
        writer.connectInput(0, reader)

        # Render
        print("render:  %s %s %s" % (writer, range_0, range_1))
        #app.render(writer, range_0, range_1) NO NEED TO CALL THE RENDER! THE WRITE AUTO EXECUTE

    except Exception as e:
        print(str(e))
        os.system("pause")


aces_to_srgb(folder)
