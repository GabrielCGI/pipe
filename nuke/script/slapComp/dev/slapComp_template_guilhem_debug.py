import sys, nuke

start_frame = int(os.getenv('START_FRAME'))
last_frame = int(os.getenv('END_FRAME'))

ocio_config_path = "R:/pipeline/networkInstall/OpenColorIO-Configs/aces_1.2/config.ocio"
os.environ['OCIO'] = ocio_config_path

# Set Nuke to use OCIO for color management
nuke.root()['colorManagement'].setValue('OCIO')
nuke.root()['OCIO_config'].setValue('aces 1.1')

# Access environment variables
chars_file = os.getenv('CHARS_FILE')
env_file = os.getenv('ENV_FILE')
output = os.getenv('OUTPUT')
outputmov = output.split('.')[0]+'.mov'



ru = nuke.nodes.Read(file = chars_file, first=start_frame, last=last_frame, on_error = 'black')

rd = nuke.nodes.Read(file = env_file, first=start_frame, last=last_frame, on_error = 'black')

m = nuke.nodes.Merge()
m.setInput(0, rd)
m.setInput(1, ru)


w = nuke.nodes.Write(file = outputmov, file_type = 'mov', colorspace = 'Output - sRGB', meta_codec = 'h264', format = 'HD_1080')
w['format'].setValue('HD_1080')
available_colorspaces = w['colorspace'].values()
print(available_colorspaces)

w.setInput(0, m)

nuke.execute("Write1", start_frame, last_frame)

