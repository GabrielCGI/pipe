import json, os, sys
import pymel.core as pm
import maya.cmds as cmds
import pymel.internal
import maya.api.OpenMaya as om
from gf_animUI import maya_tools as mayaUtils
from gf_animUI.config import version


# ----- Abstract set base class
class BaseSet(pm.nodetypes.ObjectSet):
    NODE_TYPE = 'baseSet'

    @classmethod
    def list(cls, *args, **kwargs):
        """
        Returns all instances of masterSet in the scene 
        """
        kwargs['type'] = cls.__melnode__
        return [ node for node in pm.ls(*args, **kwargs) if isinstance(node, cls)]

    @classmethod
    def _isVirtual(cls, obj, name):
        """
        checks if the node is a masterSet 
        """
        fn = pm.api.MFnDependencyNode(obj)
        try:
            if fn.hasAttribute('node_type'):
                plug = fn.findPlug('node_type')
                if plug.asString() == cls.NODE_TYPE:
                    return True
                return False
        except:
            pass
        return False

    @classmethod
    def _preCreateVirtual(cls, name, parent=None, lock=False, **kwargs):
        kwargs['name'] = name
        postKwargs = {'parent': parent, 'lock': lock}
        postKwargs.update(kwargs)
        return kwargs, postKwargs

    @classmethod
    def _createVirtual(cls, **kwargs):
        name = kwargs['name']

        # Save selection and clear it
        sel = pm.ls(sl=True)
        pm.select(clear=True)

        # Create set
        if cmds.objExists(name):
            raise NameError('Name "{}" is already used'.format(name))
        node = cmds.sets(name=name)
        return node

    @classmethod
    def _postCreateVirtual(cls, node, **kwargs):
        parent = kwargs['parent']
        lock = kwargs['lock']
        title = kwargs.get('title', None)

        node = pm.PyNode(node)

        # Get PyNode and set node_type
        node = pm.PyNode(node)
        node.addAttr('node_type', dt='string')
        node.node_type.set(cls.NODE_TYPE)
        node.node_type.lock()

        # Set Version
        node.addAttr('version', dt='string')
        node.version.set(version)
        node.version.lock()

        # Parent set
        if parent is not None:
            _ = pm.sets(parent, e=True, add=node)

        # Title
        if title is not None:
            node.addAttr('ui_title', dt='string')
            node.ui_title.set(title)

        node.setLocked(lock)

    def __api2mobject__(self):
        mSel = om.MSelectionList()
        mSel.add(self.longName())
        mObject = mSel.getDependNode(0)
        return mObject

    def __api2mfn__(self):
        return om.MFnSet(self.__apimobject__())

    def getTitle(self):
        if self.hasAttr('ui_title'):
            return self.ui_title.get()
        else:
            return self.name()

    def cleanDelete(self):
        self.setLocked(False)
        sets = [obj for obj in self.members() if isinstance(obj, pm.nodetypes.ObjectSet) and not isinstance(obj, BaseSet)]
        pm.delete(sets)
        if pm.objExists(self):
            pm.delete(self)

    def getData(self):
        data = {'name':self.name()}
        if self.hasAttr('ui_title'):
            data['title'] = self.getTitle()

        return data

    @classmethod
    def createFromData(cls, data, searchAndReplace=('','')):
        name = data.get('name').replace(searchAndReplace[0], searchAndReplace[1])
        title = data.get('title', None)
        if title is not None:
            title = title.replace(searchAndReplace[0], searchAndReplace[1])

        node = cls(name=name, title=title)
        return node

    def editParameters(self, name=None, title=None):
        if name is not None and name != self.name():
            lockState = self.isLocked()
            self.setLocked(False)
            self.rename(name)
            self.setLocked(lockState)

        if title is not None and title != self.getTitle():
            if not self.hasAttr('ui_title'):
                self.addAttr('ui_title', dt='string')

            self.ui_title.set(title)

    def getVersion(self, v=True):
        version = '0.0.0'
        if self.hasAttr('version'):
            version = self.version.get()

        if v:
            sys.stdout.write('{nodeType} {name}: {version}\n'.format(nodeType=self.NODE_TYPE, name=self.name(), version=version))
        return version


# ----- Root Set
class MasterSet(BaseSet):
    NODE_TYPE = 'masterSet'

    @classmethod
    def _postCreateVirtual(cls, node, **kwargs):
        super(MasterSet, cls)._postCreateVirtual(node, **kwargs)
        cmds.addAttr(node, ln='select_all_set', at='message')
        cmds.addAttr(node, ln='space_switch_set', at='message')

    def newTab(self, name, title=None):
        tab = TabSet(name=name, title=title, parent=self)
        return tab

    def addTab(self, tab):
        if isinstance(tab, TabSet):
            _ = pm.sets(self, e=True, add=tab)

    def removeTab(self, tab):
        if isinstance(tab, TabSet):
            if tab in getOrderedSetMembers(self):
                _ = pm.sets(self, e=True, rm=tab)

    def getTabs(self):
        tabs = TabSet.list(getOrderedSetMembers(self))
        return tabs

    def _addSelectAllSet(self):
        if self._getSelectAllSet() is None:
            allSet = pm.sets(name='ALL_{}'.format(self.name()), empty=True)
            _ = pm.sets(self, e=True, add=allSet)
            allSet.message.connect(self.select_all_set)
            return allSet

    def _getSelectAllSet(self):
        return self.select_all_set.get()

    def fillSelectAllSet(self, nodes, replace=False):
        allSet = self._getSelectAllSet()
        if allSet is None:
            allSet = self._addSelectAllSet()

        if replace:
            allSet.clear()

        for node in nodes:
            _ = pm.sets(allSet, e=True, add=node)

    def _addSpaceSwitchSet(self):
        if self._getSpaceSwitchSet() is None:
            allSet = pm.sets(name='SS_{}'.format(self.name()), empty=True)
            _ = pm.sets(self, e=True, add=allSet)
            allSet.message.connect(self.space_switch_set)
            return allSet

    def _getSpaceSwitchSet(self):
        return self.space_switch_set.get()

    def fillSpaceSwitchSet(self, attributes, replace=False):
        allSet = self._getSpaceSwitchSet()
        if allSet is None:
            allSet = self._addSpaceSwitchSet()

        if replace:
            allSet.clear()

        for at in attributes:
            _ = pm.sets(allSet, e=True, add=at)

    def cleanDelete(self):
        for tab in self.getTabs():
            tab.cleanDelete()
        super(MasterSet, self).cleanDelete()

    def getData(self):
        data = super(MasterSet, self).getData()
        data['tabs'] = [tab.getData() for tab in self.getTabs()]

        selAll = self.select_all_set.get()
        if selAll is not None:
            data['select_all_set'] = [obj.name() for obj in getOrderedSetMembers(selAll)]

        sSwitch = self.space_switch_set.get()
        if sSwitch is not None:
            data['space_switch_set'] = [obj.name() for obj in getOrderedSetMembers(sSwitch)]

        return data

    @classmethod
    def createFromData(cls, data, searchAndReplace=('','')):
        node = super(MasterSet, cls).createFromData(data, searchAndReplace)

        selAll = [pm.PyNode(obj) for obj in data.get('select_all_set', []) if pm.uniqueObjExists(obj)]
        if len(selAll):
            node.fillSelectAllSet(selAll)

        sSwitch = [pm.PyNode(obj) for obj in data.get('space_switch_set', []) if pm.uniqueObjExists(obj)]
        if len(sSwitch):
            node.fillSpaceSwitchSet(sSwitch)

        tabs = data.get('tabs', [])
        for tabData in tabs:
            tab = TabSet.createFromData(tabData, searchAndReplace)
            node.addTab(tab)

        return node


# ----- Pickers & Layers
class PickerBaseSet(BaseSet):
    NODE_TYPE = 'pickerBaseSet'
    DEFAULT_COLOR = (1.0, 0.5, 0.3)
    @classmethod
    def _postCreateVirtual(cls, node, **kwargs):
        super(PickerBaseSet, cls)._postCreateVirtual(node, **kwargs)
        color = kwargs.get('color', cls.DEFAULT_COLOR)
        cmds.addAttr(node, ln='ui_visibility', at='bool', dv=1)
        cmds.addAttr(node, ln="ui_color", at="float3", usedAsColor=True)
        cmds.addAttr(node, ln="ui_colorR", at="float", dv=color[0], parent="ui_color")
        cmds.addAttr(node, ln="ui_colorG", at="float", dv=color[1], parent="ui_color")
        cmds.addAttr(node, ln="ui_colorB", at="float", dv=color[2], parent="ui_color")

    def getNormalizedColor(self):
        return self.ui_color.get()

    def getColor(self):
        color = [int(v * 255) for v in self.getNormalizedColor()]
        return color

    def _addButtonSet(self):
        '''
        !! Intended for TabSet & LayerSet !!
        Creates a button set for this set
        '''
        if self._getButtonSet() is not None:
            raise ValueError('{} already has a ButtonSet'.format(self.name()))

        buttonSet = ButtonSet(name='BTNS_{}'.format(self.name()), parent=self)
        return buttonSet

    def _getButtonSet(self):
        '''
        !! Intended for TabSet & LayerSet !!
        Returns this set's button set
        '''
        buttonSet = ButtonSet.list(getOrderedSetMembers(self))
        if len(buttonSet):
            return buttonSet[0]
        else:
            return None

    def addButton(self, attr):
        '''
        !! Intended for TabSet & LayerSet !!
        Adds the given button attribute to this set's button set
        '''
        if not isinstance(attr, pm.Attribute):
            raise TypeError('Expected an attribute, got {} instead'.format(type(attr)))

        btnSet = self._getButtonSet()
        if btnSet is None:
            btnSet = self._addButtonSet()

        _ = pm.sets(btnSet, add=attr)

        # Add Node to Set
        node = attr.node()
        if node not in getOrderedSetMembers(self):
            _ = pm.sets(self, add=node)

    def removeButton(self, attr):
        '''
        !! Intended for TabSet & LayerSet !!
        Removes the given button attribute from this set's button set
        '''
        if attr not in self.getButtonAttributes():
            return
            #raise ValueError('{} doesn\'t belong to {}'.format(attr, self))

        _ = pm.sets(self._getButtonSet(), remove=attr)

        # Remove Node from set
        node = attr.node()
        if node in self.members():
            _ = pm.sets(self, remove=node)

    def getButtonAttributes(self):
        btnSet = self._getButtonSet()
        if btnSet is not None:
            return getOrderedSetMembers(btnSet)

        return []

    def createSelectionSet(self, nodes, name=None, select=False):
        '''
        !! Intended for TabSet & LayerSet !!
        Creates a new selection set
        '''
        if name is None:
            selSet = pm.sets(empty=True)
        else:
            selSet = pm.sets(name=name, empty=True)
        _ = pm.sets(selSet, e=True, add=nodes)
        _ = pm.sets(self, e=True, add=selSet)
        if select:
            pm.select(selSet, noExpand=True)
        return selSet

    def cleanDelete(self):
        btnSet = self._getButtonSet()
        if btnSet is not None:
            btnSet.cleanDelete()
        super(PickerBaseSet, self).cleanDelete()

    def getData(self):
        data = super(PickerBaseSet, self).getData()
        members = self.members()

        # UI Color
        data['ui_color'] = self.getNormalizedColor()

        # UI Visibility
        data['ui_visibility'] = self.ui_visibility.get()

        # Buttons
        btnSet = self._getButtonSet()
        if btnSet is not None and btnSet in members:
            members.remove(btnSet)
        if btnSet is not None:
            data['buttons'] = btnSet.getData()

        # Selection Sets
        selSets = []
        for member in members:
            if isinstance(member, pm.nodetypes.ObjectSet) and not isinstance(member, BaseSet):
                selSets.append(member)
        members = [m for m in members if m not in selSets]
        if len(selSets):
            data['select_sets'] = {selSet.name(): [node.name() for node in getOrderedSetMembers(selSet)] for selSet in
                                  selSets}

        # Set Members
        data['members'] = [obj.name() for obj in members]

        return data

    def editParameters(self, name=None, title=None, color=None):
        super(PickerBaseSet, self).editParameters(name, title)
        if color is not None and color != self.getNormalizedColor():
            self.ui_color.set(color)

    @classmethod
    def createFromData(cls, data, searchAndReplace=('','')):
        node = super(PickerBaseSet, cls).createFromData(data, searchAndReplace)
        node.ui_color.set(data.get('ui_color', cls.DEFAULT_COLOR))
        node.ui_visibility.set(data.get('ui_visibility', True))

        selSets = data.get('select_sets', {})
        if len(selSets):
            for name, members in selSets.items():
                members = [pm.PyNode(member) for member in members if pm.uniqueObjExists(member)]
                node.createSelectionSet(members, name)

        buttons = data.get('buttons', {})
        if len(buttons):
            for name, atData in buttons.items():
                if pm.uniqueObjExists(name):
                    obj = pm.PyNode(name)
                    btnAttr = addButtonAttributeInstance(obj, atData)
                    node.addButton(btnAttr)

        currentMembers = node.members()
        members = data.get('members', [])
        for name in members:
            if pm.uniqueObjExists(name):
                member = pm.PyNode(name)
                if member not in currentMembers:
                    _ = pm.sets(node, e=True, add=member)

        return node


class TabSet(PickerBaseSet):
    NODE_TYPE = 'tabSet'

    @classmethod
    def _postCreateVirtual(cls, node, **kwargs):
        title = kwargs.get('title', None)
        if title is None:
            kwargs['title'] = node

        super(TabSet, cls)._postCreateVirtual(node, **kwargs)
        cmds.addAttr(node, ln='background_image', dt='string')

    def newLayer(self, name, title=None, color=(1.0, 0.5, .3)):
        layer = LayerSet(name=name, title=title, color=color, parent=self)
        return layer

    def addLayer(self, layer):
        if isinstance(layer, LayerSet):
            _ = pm.sets(self, e=True, add=layer)

    def removeLayer(self, layer):
        if isinstance(layer, LayerSet):
            if layer in getOrderedSetMembers(self):
                _ = pm.sets(self, e=True, rm=layer)

    def getLayers(self):
        layers = LayerSet.list(getOrderedSetMembers(self))
        return layers

    def cleanDelete(self):
        for layer in self.getLayers():
            layer.cleanDelete()
        super(TabSet, self).cleanDelete()

    def getData(self):
        data = super(TabSet, self).getData()
        bgImg = self.background_image.get()
        if bgImg is not None:
            data['background_image'] = bgImg

        layers = self.getLayers()
        if len(layers):
            data['layers'] = [layer.getData() for layer in layers]

        return data

    @classmethod
    def createFromData(cls, data, searchAndReplace=('','')):
        node = super(TabSet, cls).createFromData(data, searchAndReplace)
        node.background_image.set(data.get('background_image', ''))
        layers = data.get('layers', '')
        if len(layers):
            for layerData in layers:
                layer = LayerSet.createFromData(layerData, searchAndReplace)
                node.addLayer(layer)

        return node


class LayerSet(PickerBaseSet):
    NODE_TYPE = 'layerSet'


# ----- Buttons set and functions
class ButtonSet(BaseSet):
    NODE_TYPE = 'buttonSet'

    def cleanDelete(self):
        btnAttributes = self.members()
        for attr in btnAttributes:
            removeButtonAttributeInstance(attr)
        pm.delete(self)

    def getData(self):
        return {attr.node().name(): json.loads(attr.get()) for attr in self.members()}


def createButtonAttribute(node):
    if hasButtonAttribute(node):
        return node.ui_selButtons

    node.addAttr('ui_selButtons', dt='string', multi=True)


def hasButtonAttribute(node):
    if node.hasAttr('ui_selButtons'):
        return True
    else:
        return False


def addButtonAttributeInstance(node, data):
    if not hasButtonAttribute(node):
        createButtonAttribute(node)

    attr = node.ui_selButtons
    idx = mayaUtils.nextMultiAttributeIndex(attr)
    attr[idx].set(json.dumps(data))
    return attr[idx]


def removeButtonAttributeInstance(attr):
    node = attr.node()
    attr.remove(b=True)
    mAttr = node.ui_selButtons
    if not len(mAttr.get()):
        mAttr.delete()


# ----- Utilities
def getOrderedSetMembers(objectSet):
    if not isinstance(objectSet, pm.nodetypes.ObjectSet):
        raise TypeError('Expecting an ObjectSet, got {} instead'.format(type(objectSet)))

    connections = []

    connections.extend(pm.listConnections(objectSet.dagSetMembers, source=True, destination=False, sh=True))
    connections.extend(pm.listConnections(objectSet.dnSetMembers, source=True, destination=False, sh=True))

    members = objectSet.members()

    result = []
    for node in connections:
        for n, member in enumerate(members):
            if member.node() == node:
                result.append(member)
                members.pop(n)

    return result





    return result

pymel.internal.factories.registerVirtualClass(BaseSet, nameRequired=False)
pymel.internal.factories.registerVirtualClass(MasterSet, nameRequired=False)
pymel.internal.factories.registerVirtualClass(TabSet, nameRequired=False)
pymel.internal.factories.registerVirtualClass(LayerSet, nameRequired=False)
pymel.internal.factories.registerVirtualClass(ButtonSet, nameRequired=False)