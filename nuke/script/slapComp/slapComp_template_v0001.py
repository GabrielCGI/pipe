import sys, nuke

#setting OCIO
ocio_config_path = "R:/pipeline/networkInstall/OpenColorIO-Configs/aces_1.2/config.ocio"
os.environ['OCIO'] = ocio_config_path

# Set Nuke to use OCIO for color management
nuke.root()['colorManagement'].setValue('OCIO')
nuke.root()['OCIO_config'].setValue('aces_1.1')

# variables coming from the other script
start_frame = int(sys.argv[2])
last_frame = int(sys.argv[3])
output = sys.argv[4]
outformat = sys.argv[5]
iterations = int(sys.argv[1].split('_')[-1])

w = nuke.nodes.Write(file = output, file_type = outformat, format = 'HD_1080')

if outformat == 'mov':
    w['colorspace'].setValue('color_picking')
    w['meta_codec'].setValue('avc1')
    #print(w['colorspace'].values())

#, colorspace = 'Output - sRGB\\tColorspaces/Output/Output - sRGB', meta_codec = 'avc1'

r = {}
for i in range(iterations) : 
    filepath = sys.argv[i+6].split('=')[-1]
    r[i] = nuke.nodes.Read(file = filepath, first=start_frame, last=last_frame, on_error = 'black', colorspace = 'scene_linear')

if iterations <= 2:
    print('')
    print('1 Merge Node Created')
    print('')
    me = nuke.nodes.Merge()
    me.setInput(0, r[0])
    me.setInput(1, r[1])
    w.setInput(0, me)
    
else: 
    iterations -=2
    print('')
    print(str(iterations+1)+ ' Merge Node Created')
    print('')
    me = {}
    me[0] = nuke.nodes.Merge()
    me[0].setInput(0, r[0])
    me[0].setInput(1, r[1])
    
    for i in range(iterations):
        me[i+1] = nuke.nodes.Merge()
        me[i+1].setInput(0, me[i])
        me[i+1].setInput(1, r[i+2])
        w.setInput(0, me[i+1])

print('Executing write Node...')
print('')
nuke.execute("Write1", start_frame, last_frame)
