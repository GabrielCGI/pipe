import time



reader = app.createReader(input_file)
writer = app.createWriter(output_file)
codec = writer.getParam("codecShortName")
codec.setValue("libopenh264")
premult = writer.getParam("inputPremult")
premult.setValue(2)
#The node will be accessible via app.MyWriter after this call
#We do this so that we can reference it from the command-line arguments
writer.setScriptName("MyWriter")

#The node will be accessible via app.MyReader after this call
reader.setScriptName("MyReader")


#Set the format type parameter of the Write node to Input Stream Format so that the video
#is written to the size of the input images and not to the size of the project
formatType =  writer.getParam("formatType")
formatType.setValue(0)
colorSpaceOut =  writer.getParam("ocioOutputSpaceIndex")
colorSpaceOut.setValue(105)

#Connect the Writer to the Reader
writer.connectInput(0,reader)

#When using Natron (Gui) then the render must explicitly be requested.
#Otherwise if using NatronRenderer or Natron -b the render will be automatically started
#using the command-line arguments

#To use with Natron (Gui) to start render
#app.render(writer, 0, 6)
