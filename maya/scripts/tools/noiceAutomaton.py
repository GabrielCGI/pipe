import nuke
import sys
import os

# select a read node and run script. denoise files will be created in a sub folder called denoise
# bakerbaker scripts www.aaronbaker.tv/scripts


def noice(iFile, oFile, aovs, variance, pr, sr, temporal):
    # change this to the path of the noice executable
    exe = r'C:/"Program Files"/Autodesk/Arnold/maya2022/bin/noice.exe'

    aovString = ''
    for i in aovs:
        aovString = aovString+' -l '+str(i)

    exe = exe +' -v ' + str(variance) + ' -i ' + iFile + aovString +' -pr '+ str(pr) + ' -sr ' + str(sr) + 'i' + temporal + ' -o ' + oFile
    print(exe)
    x = os.system(exe)
    # print x


def denoiseName(iFile):
    # create denoise folder
    splitPath = os.path.split(iFile)
    newFolder = os.path.join(splitPath[0],'denoise')
    if not os.path.exists(newFolder):
        os.makedirs(newFolder)

    # full path of new file name in the path of denoise folder
    x = splitPath[1].rfind('.')
    oFile = 'denoise_'+ splitPath[1][:x] + splitPath[1][x:]
    oFile = os.path.join(newFolder,oFile)

    return oFile


def getSequence(iFile):
    path = os.path.split(iFile)
    files = os.listdir(path[0])

    for i in files:
        if i == '.DS_Store':
            files.remove(i)

    fullPaths = []
    for x in files:
        x = os.path.join(path[0], x)
        if os.path.isfile(x):
            fullPaths.append(x)

    return fullPaths


def getNoiceSettings(*arg):
    p = nuke.Panel( 'Noice Settings' )

    v = 'variance'
    pr = 'patch radius'
    sr = 'search radius'
    temporal = "temporal stability"

    p.addSingleLineInput(v, '.25')
    p.addSingleLineInput(pr, '3')
    p.addSingleLineInput(sr, '9')
    p.addSingleLineInput(temporal, '0')

    # add checkboxes for AOV's to denoise

    success = p.show()

    print success
    if success:
        v = p.value(v)
        pr = p.value(pr)
        sr = p.value(sr)
        temporal = p.value(temporal)

    settings = [v, pr, sr, temporal]

    return (settings)


def getAovs( node ):
    denoiseAovs = []
    channels = node.channels()
    layers = list( set([c.split('.')[0] for c in channels]) )
    layers.sort()
    # CREATE SIMPLE PANEL TO MAP THE BUFFERS
    pAov = nuke.Panel( 'Select AOVs To Denoise' )
    for i in layers:
        pAov.addBooleanCheckBox( i, False)
    if not pAov.show():
        return

    for i in layers:
        if pAov.value(i):
            # print i
            denoiseAovs.append(i)

    return denoiseAovs


def runNoice():
    # get path from slected node
    try:
        node = nuke.selectedNode()
    except ValueError:  # no node selected
        print 'error no node selected'
        nuke.message("No read node selected")
        return
        # sys.exit()
    else:
        if node.Class() == 'Read':
            iFile = node['file'].value()
            print 'iFile:', iFile
            # runNoice()
            pass
        else:
            print 'Error'
            nuke.message("Select one read node.")
            # sys.exit()
            return


    # get settings from dialog and then run noice on selected read node
    settings = getNoiceSettings()
    vv = settings[0]
    pr = settings[1]
    sr = settings[2]
    temporal = settings[3]
    print 'noice settings: ', settings
    files = getSequence(iFile)
    num = len(files)
    print num, ' Files to denoise'

    aovs = getAovs(node)
    t = nuke.ProgressTask("Running Noice")

    for i in files:
        if t.isCancelled():
            raise RuntimeError("Cancelled")
            # t = None
        print 'running noice on: ' + i
        oFile = denoiseName(i)
        noice(i, oFile, aovs, vv, pr, sr, temporal)
        print 'Done'

        # update progress bar
        t.setProgress(int(100 * ((files.index(i)-1) / num)))
        t.setMessage("Created %d of %d" % (files.index(i)+1, num))
runNoice()
