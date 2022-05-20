# Sample script that applies an OpenColorIO LUT to an image sequence, which are then encoded to a video.
#
# There are two options for specifying the OCIO LUT to apply:
# 1.  Specify the path to the config.ocio file (as additional argument ocioConfig) and the names of the input
#     (colorIn) and output (colorOut) color spaces.
# 2.  Specify the full path to a single LUT file (as additional argument lut).
#
# Sample additional args:
#    ocioConfig="//YourDeadlineRepository7/draft/ocio-configs/nuke-default/config.ocio" colorIn="linear" colorOut="Cineon"
# or:
#    lut="//YourDeadlineRepository7/draft/ocio-configs/nuke-default/luts/cineon.spi1d"

import Draft
import sys  # To access commmand line arguments.  Deadline sends script parameters as command line arguments.
from DraftParamParser import *  # Functions to process command line arguments for Draft.

# Parameter names for optional OpenColorIO parameters:
paramOCIOEnv = 'ocioConfig'
paramOCIOColorSpaceIn = 'colorIn'
paramOCIOColorSpaceOut = 'colorOut'
paramOCIOLut = 'lut'

# The argument name/types we're expecting from the command line arguments or Deadline.
expectedTypes = dict()
expectedTypes[ 'inFile' ] = '<string>'
expectedTypes[ 'outFile' ] = '<string>'
expectedTypes[ 'frameList' ] = '<string>'
#expectedTypes[ paramOCIOEnv ] = '<string>'             # ****** uncomment this line if you want the parameter to be mandatory rather than optional
#expectedTypes[ paramOCIOColorSpaceIn ] = '<string>'    # ****** uncomment this line if you want the parameter to be mandatory rather than optional
#expectedTypes[ paramOCIOColorSpaceOut ] = '<string>'   # ****** uncomment this line if you want the parameter to be mandatory rather than optional
#expectedTypes[ paramOCIOLut ] = '<string>'         # ****** uncomment this line if you want the parameter to be mandatory rather than optional

# Parse the command line arguments.
params = ParseCommandLine( expectedTypes, sys.argv )    # params now contains a dictionary of the parameters initialized to values from the command line arguments.
inFilePattern = params['inFile']    # The pattern that the input files follow, for example frame_name_###.ext, where ### represents a three digit frame number.
frames = FrameRangeToFrames( params['frameList'] )  # Get a list of the individual frames we are to process

#Bloom edit
params[ paramOCIOEnv ] = "R:/pipeline/networkInstall/OpenColorIO-Configs/aces_1.2/config.ocio"
params[ paramOCIOColorSpaceIn ] = "ACES - ACEScg"
params[ paramOCIOColorSpaceOut ] = "Output - Rec.709"
#Bloom edit end

# Set up OCIO environment and fetch LUT
if paramOCIOEnv in params:
    Draft.LUT.SetOCIOConfig( params[ paramOCIOEnv ] )
lut = None
if ( paramOCIOColorSpaceIn in params ) and ( paramOCIOColorSpaceOut in params ):
    lut = Draft.LUT.CreateOCIOProcessor( params[ paramOCIOColorSpaceIn ], params[ paramOCIOColorSpaceOut ] )
elif paramOCIOLut in params:
    lut = Draft.LUT.CreateOCIOProcessorFromFile( params[ paramOCIOLut ] )

# Initialize the video encoder.
frame = Draft.Image.ReadFromFile( ReplaceFilenameHashesWithNumber( inFilePattern, frames[0] ) ) # use the first frame to determine video size
encoder = Draft.VideoEncoder( params['outFile'], 24, frame.width, frame.height )

# Process each of the frames in the list of frames (including the first, which hasn't yet been added to the encoder).
progressCounter = 0;
for currFrame in frames:
    # Read in the frame.
    currFile = ReplaceFilenameHashesWithNumber( inFilePattern, currFrame )
    frame = Draft.Image.ReadFromFile( currFile )

    if lut is not None:
        lut.Apply( frame )  # ****** apply the OpenColorIO LUT to the frame

    # Add the frame to the encoder.
    encoder.EncodeNextFrame( frame )

    progressCounter = progressCounter + 1
    progress = progressCounter * 100 / len( frames )
    print( "Progress: %i%%" % progress )

# Finalize and save the resulting video.
encoder.FinalizeEncoding()
