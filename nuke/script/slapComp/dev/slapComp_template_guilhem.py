import sys, nuke

#setting OCIO
ocio_config_path = "R:/pipeline/networkInstall/OpenColorIO-Configs/aces_1.2/config.ocio"
os.environ['OCIO'] = ocio_config_path

# Set Nuke to use OCIO for color management
nuke.root()['colorManagement'].setValue('OCIO')
nuke.root()['OCIO_config'].setValue('aces_1.1')

outformat = 'HD_1080'

# variables coming from the other script
start_frame = int(sys.argv[2])
last_frame = int(sys.argv[3])
output = sys.argv[4]
outputmov = output.split('.')[0]+'.mov'
iterations = int(sys.argv[1].split('_')[-1])

w = nuke.nodes.Write(file = outputmov, file_type = 'mov', colorspace = 'Colorspaces/Ouput/Output - sRGB', meta_codec = 'avc1', format = outformat)

r = {}
for i in range(iterations) : 
    filepath = sys.argv[i+5].split('=')[-1]
    r[i] = nuke.nodes.Read(file = filepath, first=start_frame, last=last_frame, on_error = 'black',  format = outformat)

if iterations <= 2:
    print('')
    print('1 Merge Node Created')
    me = nuke.nodes.Merge()
    me.setInput(0, r[1])
    me.setInput(1, r[0])
    w.setInput(0, me)
    
else: 
    iterations -=2
    print('')
    print(str(iterations+1)+ ' Merge Node Created')
    me = {}
    me[0] = nuke.nodes.Merge()
    me[0].setInput(0, r[1])
    me[0].setInput(1, r[0])
    
    for i in range(iterations):
        me[i+1] = nuke.nodes.Merge()
        me[i+1].setInput(0, me[i])
        me[i+1].setInput(1, r[i+2])
        w.setInput(0, me[i+1])

nuke.execute("Write1", start_frame, last_frame)
