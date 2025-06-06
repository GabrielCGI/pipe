import pymel.core as pm
import pymel.core.datatypes as dt
import maya.api.OpenMaya as om
from maya import cmds
from gf_animtools.utilities import maya_api
from gf_animtools.tools.naming_convention import conventions


class RigObjectBase(object):
    NODE_TYPE = 'rigObject'

    @classmethod
    def list(cls, *args, **kwargs):
        kwargs['long'] = True
        kwargs['type'] = 'transform'
        transforms = cmds.ls(*args, **kwargs)

        result = []
        for t in transforms:
            if cls.is_valid(t):
                result.append(cls(t))

        return result

    @classmethod
    def is_valid(cls, node_name):
        fn = maya_api.getMFnDependencyNode(node_name)
        if fn.hasAttribute('node_type'):
            plug = fn.findPlug('node_type', False)
            if plug.asString() == cls.NODE_TYPE:
                return True
        return False

    def __init__(self, node_name):
        if not self.is_valid(node_name):
            raise TypeError('{} is not a {} node'.format(node_name, self.NODE_TYPE))

        self.node_name = node_name
        self.node = pm.PyNode(node_name)

    def __repr__(self):
        return '{} <{}>'.format(self.node.name(), self.__class__.__name__)

    def __str__(self):
        return self.node.name()

    def __getattr__(self, item):
        attr = getattr(self.node, item)
        return attr

    def namespace(self):
        node_name = self.node.name()
        if ':' in node_name:
            ns = node_name.rsplit(':', 1)[0]
            return ns
        else:
            return ''


class RigRoot(RigObjectBase):
    NODE_TYPE = 'rigRoot'

    def __init__(self, node_name):
        super(RigRoot, self).__init__(node_name=node_name)

    # ----- Parameters ----- #
    @property
    def rigName(self):
        nodeName = self.node.name()

        # Remove namespaces
        nsSplit = nodeName.rsplit(':', 1)
        if len(nsSplit) == 2:
            nodeName = nsSplit[1]

        name = nodeName
        return name

    @property
    def namingConvention(self):
        if self.hasAttr('naming_convention'):
            convention = self.naming_convention.get()
        else:
            convention = 'default'

        return conventions.get(convention, 'default')()

    # ----- Default Groups ----- #
    @property
    def ctrGp(self):
        return self.node.Controllers.get()

    @property
    def rigGp(self):
        return self.node.Rigging.get()

    @property
    def skGp(self):
        return self.node.Skeleton.get()

    @property
    def mshGp(self):
        return self.node.Mesh.get()

    @property
    def locGp(self):
        return self.node.Locators.get()

    # ----- Controllers ----- #
    @property
    def ctr_world(self):
        return self.node.ctrGp.World.get()

    @property
    def ctr_walk(self):
        return self.node.ctrGp.Walk.get()

    @property
    def ctr_root(self):
        return self.node.ctrGp.Root.get()

    @property
    def controllers(self):
        return self.node.ctr_all.get()

    # ----- Modules ----- #
    @property
    def modules(self):
        return self.node.rigGp.modules.get()


class ModGroup(RigObjectBase):
    NODE_TYPE = 'modBase'

    def __init__(self, node_name):
        super(ModGroup, self).__init__(node_name=node_name)

    # ----- Parameters ----- #
    @property
    def mod_name(self):
        return self.node.modName.get()

    @property
    def mod_suffix(self):
        return self.node.modSuffix.get()

    @property
    def rig(self):
        return RigRoot(self.node.rigRoot.get().name(long=True))

    def _hasUserAttr(self):
        return self.node.hasAttr('userAttributes')

    def getUserAttr(self):
        if self._hasUserAttr():
            uaStr = self.node.userAttributes.get()
            result = {}
            for couple in uaStr.split(';'):
                if not len(couple):
                    break
                k, v = couple.split('=',1)
                if v[0] == '"' and v[-1] == '"':
                    result[k] = v[1:-1]
                else:
                    result[k] = int(v)
            return result
        else:
            return {}

    # ----- Default Groups ----- #
    @property
    def ctrGp(self):
        return self.node.Controllers.get()

    @property
    def skGp(self):
        return self.node.Skeleton.get()

    @property
    def locGp(self):
        return self.node.Locators.get()

    # ----- Controllers ----- #
    @property
    def set_controllers(self):
        if self.node.hasAttr('dataSet'):
            dSet = self.node.dataSet.get()
            if len(dSet):
                return dSet[1]
        return None

    @property
    def controllers(self):
        if self.set_controllers is not None:
            controllers = self.set_controllers.members()
            controllers = [RigControl(c.name(long=True)) for c in controllers]
            return controllers
        else:
            return []


class RigControl(RigObjectBase):
    NODE_TYPE = 'rigControl'

    @classmethod
    def findFromName(cls, name, fromList=None):
        if fromList is None:
            fromList = cls.list()
        else:
            fromList = [obj for obj in fromList if isinstance(obj, cls)]

        for obj in fromList:
            n = obj.node.ctrName.get()
            if n == name:
                return obj
        return None

    def __init__(self, node_name):
        super(RigControl, self).__init__(node_name=node_name)