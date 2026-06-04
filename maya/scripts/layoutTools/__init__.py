



def _instantMaya():
    from shiboken6 import wrapInstance
    import qtpy.QtWidgets as qt
    from maya import OpenMayaUI

    return wrapInstance(int(OpenMayaUI.MQtUtil.mainWindow()), qt.QWidget)

def camGateOff():
    from importlib import reload
    from . import edit_camera
    reload(edit_camera)

    edit_camera.editCamGate([0, 0, 0, 1, 1])

def camGateOn():
    from importlib import reload
    from . import edit_camera
    reload(edit_camera)

    edit_camera.editCamGate([0, 1, 1, 1.15, 1])

def freeCam():
    from importlib import reload
    from . import edit_camera
    reload(edit_camera)

    edit_camera.createFreeCamFromRig()

def freeCamtoRig(*args):
    from importlib import reload
    from . import edit_camera
    reload(edit_camera)

    edit_camera.freeCamtoRig(*args)



def editTimeShot():
    from importlib import reload
    from . import edit_timeShots
    reload(edit_timeShots)

    windowOffset = edit_timeShots.offsetShot(_instantMaya())
    windowOffset.show()



def manageShots():
    from importlib import reload
    from . import manage_shots
    reload(manage_shots)

    windowMS = manage_shots.ManageShotsSequence(_instantMaya())
    windowMS.show()



def exportAsLayer():
    from importlib import reload
    from . import export_shot_layer
    reload(export_shot_layer)

    windowESL = export_shot_layer.ExportAsLayer(_instantMaya())
    windowESL.show()


def splitShots():
    pass