


def mainRun(*args):
    from .edit_hearchie import EditHierarchy

    from maya import OpenMayaUI
    from shiboken6 import wrapInstance
    from PySide6.QtWidgets import QWidget
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    instance = wrapInstance(int(main_window_ptr), QWidget)

    data = EditHierarchy(instance)
    data.show()