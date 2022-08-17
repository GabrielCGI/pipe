import subprocess
import nuke


def copy2clip(txt):
    cmd='echo '+txt.strip()+'|clip'
    return subprocess.check_call(cmd, shell=True)

def getAovs( node ):
    denoiseAovs = []
    channels = node.channels()
    layers = list( set([c.split('.')[0] for c in channels]) )
    layers.sort()
    # CREATE SIMPLE PANEL TO MAP THE BUFFERS
    pAov = nuke.Panel( 'Select AOVs To Denoise' )

    blacklist = ["crypto","noice","variance","other","Z","rgba"]
    for i in layers:
        skip=0
        for black in blacklist:
            if black in i:
                skip=1
        if skip ==0:
            if "RGBA" in i:
                pAov.addBooleanCheckBox( i, True)
            else:
                pAov.addBooleanCheckBox( i, False)
    if not pAov.show():
        return

    for i in layers:
        if pAov.value(i):
            # print i
            denoiseAovs.append(i)

    return denoiseAovs


def run():
    node = nuke.selectedNode()
    aovs = getAovs( node )
    str=''
    for aov in aovs:
        if aov.startswith('RGBA_'):
            aov = aov.split('RGBA_')[-1]
        str=str + aov +" "
    print(str)
    copy2clip(str)
