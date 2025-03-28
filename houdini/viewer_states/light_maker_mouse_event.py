"""
State:          Light Maker Mouse Events
State type:     light_maker_mouse_events
Description:    Light Maker Mouse Events
Author:         samuelh
Date Created:   September 30, 2019 - 18:01:47
"""


import hou
from lightstate import *


class DataInterface(lightdata.LightStateData):

    DISTANCE_THRESHOLD = .001

    def __init__(self, node):
        self._node = node
        super(DataInterface, self).__init__(node)

    def _read_val(self, parmname):
        # Light::2.0 LOP has many parms that are the same as the old parms,
        # but with an 'inputs:' prefix. To work with Light::1.0, we just need
        # to strip off this prefix.
        try:
            return self._node.evalParm(hou.text.encode(parmname))
        except:
            if parmname.startswith('inputs:'):
                return self._node.evalParm(hou.text.encode(parmname[7:]))

    def _read_val_str(self, parmname):
        if parmname == "primstr":
            is_create_mode = not self.isEditing()
            parmname = "primpath" if is_create_mode else "primpattern"
        elif parmname == "lighttype":
            # If the node doesn't have a "lighttype" parameter, use the
            # primitive type instead (which is generally going to be equal
            # to the light type, except for point lights).
            if self._node.parm(parmname) is None:
                return self._node.parm("primtype").evalAsString()

        return self._node.parm(parmname).evalAsString()

    def _read_vec3(self, parmname):
        parmname = hou.text.encode(parmname)
        return hou.Vector3(self._node.evalParmTuple(parmname))

    def _update_or_read_val(self, parmname, val = None):
        if val is not None:
            self.__setParmValue(parmname, self._node.parm, val)
        return self._read_val(parmname)

    def _update_or_read_vec3(self, parmname, val = None):
        if val is not None:
            self.__setParmValue(parmname, self._node.parmTuple, val)
        return self._read_vec3(parmname)

    def __setParmValue(self, parmname, parm_fn, val):
        try:
            parm_fn(hou.text.encode(parmname)).set(val)
        except:
            if parmname.startswith('inputs:'):
                try:
                    parm_fn(parmname.split(':')[1]).set(val)
                except:
                    pass


    def s(self, vals=None):
        # Account for the uniform scale factor.
        if vals is not None:
            uniform_scale = self.scale()
            vals = [val/uniform_scale for val in vals]
        return super(DataInterface, self).s(vals)

    def isEditing(self):
        node_action = self._node.evalParm("createprims")
        return node_action == 0

    def oporder(self):
        return self._node.parm("xn__xformOptransform_51a").evalAsString()

    def xord(self):
        return self._node.parm("xOrd").evalAsString()

class State(lightstate.LightState):
    def onEnter(self, kwargs):
        """
        Executed when state is entered.
        """

        node = kwargs['node']
        node.addEventCallback([hou.nodeEventType.ParmTupleChanged], self.updateNodeParmCB)

        self.lastScale = 50
        self.defaultScale = 50
        self.initialState = False
        
        data = DataInterface(node)

        super(State, self).onEnter(kwargs, data)

        # For distant lights rotation handles make more sense as a default.
        if node.type().name().startswith("distantlight"):
            self.scene_viewer.enterRotateToolState()

    def onExit(self, kwargs):
        node = kwargs.get('node', None)
        if node:
            # If the node is deleted it's callbacks should be cleaned up anyways.
            node.removeEventCallback([hou.nodeEventType.ParmTupleChanged], self.updateNodeParmCB)

    def onMouseEvent(self, kwargs):
        """ Process mouse and tablet events
        """
        
        super().onMouseEvent(kwargs)
                
        ui_event = kwargs["ui_event"]
        reason = ui_event.reason()
        
        if reason == hou.uiEventReason.Start:
            copnet_path = kwargs['node'].parm('copnet_path').eval()
            copnet = hou.node(copnet_path)
            
            if not copnet:
                return
                
            parm_pixelscale = copnet.parm('pixelscale')
            parm_setpixelscale = copnet.parm('setpixelscale')
            
            if not parm_pixelscale or not parm_setpixelscale:
                return
                
            currentScale = parm_pixelscale.eval()
            if currentScale != self.defaultScale:
                self.initialState = parm_setpixelscale.eval()
                self.lastScale = currentScale
                
            parm_pixelscale.set(self.defaultScale)
            parm_setpixelscale.set(True)

        elif reason == hou.uiEventReason.Changed:
            copnet_path = kwargs['node'].parm('copnet_path').eval()
            copnet = hou.node(copnet_path)
            
            if not copnet:
                return
                
            parm_pixelscale = copnet.parm('pixelscale')
            parm_setpixelscale = copnet.parm('setpixelscale')
            
            if not parm_pixelscale or not parm_setpixelscale:
                return
                
            parm_pixelscale.set(self.lastScale)
            parm_setpixelscale.set(self.initialState)

        # Must return True to consume the event
        return False
            
def createViewerStateTemplate():
    """ Mandatory entry point to create and return the viewer state
        template to register. """

    state_typename = "light_maker_mouse_events"
    state_label = "Light Maker Mouse Events"
    state_cat = hou.lopNodeTypeCategory()

    template = hou.ViewerStateTemplate(state_typename, state_label, state_cat)
    template.bindFactory(State)
    lightstate.LightStateHandle.bindHandles(template)
    hotkey_definitions = hou.PluginHotkeyDefinitions()
    lightstate.LightState.registerHotkeys(hotkey_definitions,
                                          state_typename, state_cat)
    template.bindHotkeyDefinitions(hotkey_definitions)
    lightstate.LightState.bindMenu(template)
    lightstate.LightState.bindParameters(template)
    template.bindIcon("LOP_light")

    return template
