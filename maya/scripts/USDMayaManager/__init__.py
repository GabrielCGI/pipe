



def mainRun(*args):
    import os 
    from importlib import reload
    from .UI import UI_maya_polices_main
    reload(UI_maya_polices_main)

    from maya import OpenMayaUI
    from shiboken6 import wrapInstance
    from PySide6.QtWidgets import QWidget
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    instance = wrapInstance(int(main_window_ptr), QWidget)

    window = UI_maya_polices_main.UIMainMaya(instance)
    
    style = os.path.join(os.path.dirname(__file__), "configs", "style.qss")
    with open(style, "r") as f:
        data = f.read()

    window.setStyleSheet(data)
    window.show()

    return window