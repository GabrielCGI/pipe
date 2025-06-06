from gf_animtools.tools import py_tools as pyUtils
import re
leftSide = '_L'
rightSide = '_R'
midSide = '_Mid'
topSide = '_Top'
btmSide = '_Btm'
sides = [leftSide, rightSide]


def conformName(name, type):
    splitName = name.split('_')
    suffix = ''

    # Get Btm/Top suffix first
    if len(splitName) > 1:
        for sfx in ['Btm', 'Top']:
            if sfx in splitName:
                suffix += '_' + sfx.capitalize()
                splitName.remove(sfx)

    # Get L/R/Mid suffix
    if len(splitName) > 1 and splitName[-1] in ['L', 'R', 'Mid']:
        suffix += '_' + splitName.pop(-1).capitalize()

    namesList = []
    incList = []
    # Separate words & numbers
    for nme in splitName:
        if nme.isalpha():
            namesList.extend(pyUtils.camelCaseSplit(nme))
        else:
            incList.append(nme)

    namesStr = pyUtils.listToCamelCase(namesList)
    incStr = ''

    # Set object type
    if type is None:
        typeStr = ''
    else:
        typeStr = '_' + type
    if len(incList):
        incStr = '_' + '_'.join(incList)

    # Build result
    newName = namesStr + incStr + typeStr

    return newName, suffix


class BaseConvention(object):
    NAME = 'Default'

    def __init__(self):
        '''
        Input Convention : <name>InputName<*increments>_01_02_03<*objectType>_Type<*vSide>_Btm|_Top<*hSide>_L|_Mid|_R
        '''
        super(BaseConvention, self).__init__()
        self._inputRegex = r'^(?P<name>[a-zA-Z]+)(?P<increments>(?:_*\d+)*)?(?P<suffixes>(?:_*[a-zA-Z]*)+)?$'
        self._inputSuffixRegex = r'^(?P<objectType>.*?)(?=(?:_Btm|_Top|_L$|_R$|_Mid$|$))(?P<vSide>_Btm|_Top)?(?P<hSide>(?:_L$|_Mid$|_R$)$)?'

    @property
    def inputSides(self):
        return {'_L': 'left',
                '_R': 'right',
                '_Mid': 'middle',
                '_Top': 'top',
                '_Btm': 'bottom'}

    # ----- Name dictionaries ----- #
    @property
    def sides(self):
        '''
        Override the dict values to implement your own side names
        :return: dict
        '''
        return {'left': '_L',
                'right': '_R',
                'middle': '_Mid',
                'top': '_Top',
                'bottom': '_Btm'}

    @property
    def commonNodes(self):
        '''
        Dict representing the short names for Maya common nodes
        Override the dict to implement your own short names
        :return: dict
        '''
        return {'plusMinusAverage': 'pma',
                'multiplyDivide': 'mtp',
                'vectorProduct': 'vpd',
                'distanceBetween': 'dbn',
                'condition': 'cd',
                'clamp': 'clp',
                'blendColors': 'bc',
                'multMatrix': 'mmx',
                'decomposeMatrix': 'dmx',
                'blendTwoAttr': 'btr',
                'pointOnSurfaceInfo': 'posi',
                'aimConstraint': 'aimConstraint',
                'remapValue': 'rmp',
                'axisAngleToQuat': 'aaq',
                'floatMath': 'fm',
                'angleBetween': 'ab'}

    @property
    def specialObjects(self):
        '''
        Dict representing the names for special rig objects like controllers, joints, etc...
        Override the dict values to implement your own names
        :return: dict
        '''
        return {'controller': 'Ctr',
                'offsetNode': 'Offset',
                'poseNode': 'Pose',
                'subNode': 'Sub',
                'joint': 'Sk',
                'locator': 'Loc',
                'mesh': 'Msh',
                'objectSet': 'Set',
                'group': 'Grp',
                'ctr_group': 'Ctr_Grp',
                'rig_group': 'Rig_Grp',
                'joint_group': 'Sk_Grp',
                'mesh_group': 'Msh_Grp',
                'locator_group': 'Loc_Grp'}

    @property
    def defaultObjectSets(self):
        '''
        Dict representing the names for the rig' default objectSets.
        Override the dict values to implement your own names
        :return: dict
        '''
        return {'data': 'Data_Set',
                'for_anim': 'Controllers',
                'skinning': 'Skinning_Set',
                'meshes': 'Meshes_Set'}

    @property
    def defaultControllers(self):
        '''
        Dict representing the names for the rig's default controllers.
        Override the dict values to implement your own names
        :return: dict
        '''
        return {'world': 'World',
                'walk': 'Walk',
                'root': 'Root'}

    @property
    def defaultAttributes(self):
        '''
        Dict representing the rig's default attribute names.
        Override the dict values to implement your own names.
        :return: dict
        '''
        return {'IKFK': 'IKFK',
                'spaceSwitch': 'follow',
                'softIk': 'soft'}

    def computeName(self, inputName, objType=None, skip=None):
        '''
        Decomposes the input name in different sections, translate them and combine them
        :param inputName: string matching the input naming convention
        :param objType: string corresponding to a key in commonNodes or specialObjects
        :return: 
        '''

        if skip is None:
            skip = []
        # Decompose the inputName and get a dict with the different sections
        inputDic = self.getDecomposedInputDic(inputName)

        # if inputDic is False, the inputName is not valid
        if inputDic is False:
            return False

        # Treat each element independently to convert them to string or None

        dic = {'name': self.translateName(inputDic['name']),
               'increments': self.translateIncrements(inputDic['increments']),
               'objectType': inputDic['objectType'],
               'vSide': self.translateSide(inputDic['vSide']),
               'hSide': self.translateSide(inputDic['hSide'])}

        if objType is not None:
            dic['objectType'] = self.getObjectTypeSuffix(objType)

        # Removed skipped keys
        for k in skip:
            if k in dic:
                dic[k] = None

        result = self.combineName(**dic)

        return result

    def combineName(self, name, increments='', objectType=None, vSide=None, hSide=None):
        result = name + increments

        if objectType is not None:
            result += '_' + objectType

        if vSide is not None:
            result += vSide

        if hSide is not None:
            result += hSide

        return result

    # ----- Translation ----- #
    def getObjectTypeSuffix(self, value, default=None):
        '''
        looks for the object type corresponding to the value parameter, in that order : commonNodes, specialObjects, defaultObjectSets
        :param value: string
        :param default: default type. If None, default == value
        :return: string
        '''
        if default is None:
            default = value

        return self.specialObjects.get(value, self.commonNodes.get(value, self.defaultObjectSets.get(value, default)))

    def translateSide(self, inputSide):
        '''
        Translates the input side section. Override to implement your own translation
        :param inputSide: a string matching the inputSides dict 
        :return: sides dict key
        '''
        if inputSide is None:
            return None

        if inputSide not in self.inputSides:
            raise ValueError('{} is not a valid input side'.format(inputSide))

        side = self.sides.get(self.inputSides[inputSide])
        return side

    def translateName(self, inputName):
        '''
        Translates the input name section. Override to implement your own translation
        :param inputName: a string, preferably in camelCase or UpperCamelCase
        :return: the input string converted into UpperCamelCase
        '''
        if not len(inputName):
            return inputName
        if len(inputName) == 1:
            return inputName.capitalize()

        inputName = inputName[0].capitalize() + inputName[1:]

        return inputName

    def translateIncrements(self, inputIncrements):
        '''
        Translates the input increments into a string. Override to implement your own translation
        :param inputIncrements: tuple
        :return: combined string of all increments separated with '_'
        '''
        inputIncrements = [str(int(i)).zfill(2) for i in inputIncrements]
        if len(inputIncrements):
            increments = '_' + '_'.join(inputIncrements)
        else:
            increments = ''

        return increments

    # ----- Regex decomposition stuff ----- #
    def decomposeInput(self, value):
        result = re.match(self._inputRegex, value)

        if result is None:
            return ()

        return result.group('name'), result.group('increments'), result.group('suffixes')

    def decomposeIncrements(self, value):
        if value is None or not len(value):
            return ()

        if value[0] == '_':
            value = value[1:]

        return value.split('_')

    def decomposeSuffixes(self, value):
        result = re.match(self._inputSuffixRegex, value)

        if result is None:
            return None, None, None

        objectType = result.group('objectType')
        if len(objectType):
            if objectType[0] == '_':
                objectType = objectType[1:]

        if objectType == '':
            objectType = None

        return objectType, result.group('vSide'), result.group('hSide')

    def getDecomposedInputDic(self, inputName):
        decInput = self.decomposeInput(inputName)
        if not len(decInput):
            return False

        name = decInput[0]
        increments = self.decomposeIncrements(decInput[1])
        suffixes = self.decomposeSuffixes(decInput[2])

        objectType = suffixes[0]
        vSide = suffixes[1]
        hSide = suffixes[2]

        return {'name': name,
                'increments': increments,
                'objectType': objectType,
                'vSide': vSide,
                'hSide': hSide}

    # ----- Module Specific Name Dictionnaries ----- #
    def getLimbsJntNames(self, typeId):
        if typeId:
            return {'clav': 'HipClav',
                    'shoulder': 'Hip',
                    'elbow': 'Knee',
                    'hand': 'Foot'}
        else:
            return {'clav': 'ArmClav',
                    'shoulder': 'Shoulder',
                    'elbow': 'Elbow',
                    'hand': 'Hand'}

    def getLimbTypeName(self, typeId):
        if typeId:
            return 'Arm'
        else:
            return 'Leg'

    def getLimbsCtrNames(self, typeId, name, extraName):
        jNames = self.getLimbsJntNames(typeId)

        dic = {'fk_shoulder': 'Fk' + jNames['shoulder'] + extraName,
               'fk_elbow': 'Fk' + jNames['elbow'] + extraName,
               'fk_hand': 'Fk' + jNames['hand'] + extraName,
               'pole_vector': 'Pv' + jNames['elbow'] + extraName,
               'ik_hand': jNames['hand'] + extraName,
               'limb_options': name + 'Options' + extraName,
               'bend_shoulder': 'Bend' + jNames['shoulder'] + extraName,
               'bend_elbow': 'Bend' + jNames['elbow'] + extraName,
               'bend_hand': 'Bend' + jNames['hand'] + extraName,
               'clav': jNames['clav'] + extraName}
        return dic


class TTConvention(BaseConvention):
    NAME = 'TTRig'

    def __init__(self):
        super(TTConvention, self).__init__()

    # ----- Name dictionaries ----- #
    @property
    def sides(self):
        sides = super(TTConvention, self).sides
        sides['top'] = 'Up'
        sides['bottom'] = 'Dn'
        return sides

    @property
    def defaultControllers(self):
        defaultControllers = super(TTConvention, self).defaultControllers
        defaultControllers['root'] = 'Fly'
        return defaultControllers

    @property
    def specialObjects(self):
        specialObjects = super(TTConvention, self).specialObjects
        specialObjects['controller'] = 'c'
        specialObjects['joint'] = 'sk'
        return specialObjects

    def translateName(self, inputName):
        if not len(inputName):
            return inputName
        if len(inputName) == 1:
            return inputName.capitalize()

        inputName = inputName[0].lower() + inputName[1:]

        return inputName

    def translateIncrements(self, inputIncrements):
        increments = [str(int(i)) for i in inputIncrements]
        return '_'.join(increments)

    def combineName(self, name, increments='', objectType=None, vSide=None, hSide=None):
        result = name + increments

        if objectType is not None:
            result = objectType + '_' + result

        if vSide is not None:
            result += vSide

        if hSide is not None:
            result += hSide

        return result

    # ----- Module Specific Name Dictionnaries ----- #
    def getLimbsJntNames(self, typeId):
        if typeId:
            return {'clav': 'hipClav',
                    'shoulder': 'hip',
                    'elbow': 'knee',
                    'hand': 'foot'}
        else:
            return {'clav': 'clav',
                    'shoulder': 'shoulder',
                    'elbow': 'elbow',
                    'hand': 'hand'}

    def getLimbsCtrNames(self, typeId, name, extraName):
        jNames = self.getLimbsJntNames(typeId)

        dic = {'fk_shoulder': jNames['shoulder'] + extraName,
               'fk_elbow': jNames['elbow'] + extraName,
               'fk_hand': jNames['hand'] + extraName,
               'pole_vector': 'pv' + jNames['hand'].capitalize() + extraName,
               'ik_hand': jNames['hand'] + extraName + 'IK',
               'limb_options': name.lower() + 'Switch' + extraName,
               'bend_shoulder': jNames['shoulder'] + 'Bend' + extraName,
               'bend_elbow': jNames['elbow'] + 'Point' + extraName,
               'bend_hand': jNames['hand'] + 'Bend' + extraName,
               'clav': jNames['clav'] + extraName}
        return dic


class SupaConvention(BaseConvention):
    NAME = 'Supa'

    def __init__(self):
        super(SupaConvention, self).__init__()

    @property
    def sides(self):
        return {'left': 'l_',
                'right': 'r_',
                'middle': 'm_',
                'top': 'top_',
                'bottom': 'btm_'}

    @property
    def specialObjects(self):
        dic = super(SupaConvention, self).specialObjects
        dic['controller'] = 'anim'
        dic['offsetNode'] = 'null'
        dic['poseNode'] = 'pose'
        dic['subNode'] = 'sub'
        return dic

    @property
    def defaultControllers(self):
        '''
        Dict representing the names for the rig's default controllers.
        Override the dict values to implement your own names
        :return: dict
        '''
        return {'world': 'position',
                'walk': 'traj',
                'root': 'fly'}

    def translateIncrements(self, inputIncrements):
        increments = [str(int(i)) for i in inputIncrements]
        return '_'.join(increments)

    def translateName(self, inputName):
        return '_'.join([n.lower() for n in pyUtils.camelCaseSplit(inputName)])

    def getLimbTypeName(self, typeId):
        name = super(SupaConvention, self).getLimbTypeName()
        return name.lower()

    def getLimbsJntNames(self, typeId):
        if typeId:
            return {'clav': 'hip',
                    'shoulder': 'thigh',
                    'elbow': 'knee',
                    'hand': 'foot'}
        else:
            return {'clav': 'clavicle',
                    'shoulder': 'shoulder',
                    'elbow': 'elbow',
                    'hand': 'hand'}

    def getLimbsCtrNames(self, typeId, name, extraName):
        jNames = self.getLimbsJntNames(typeId)

        dic = {'fk_shoulder': name + extraName + '_1',
               'fk_elbow': name + extraName + '_2',
               'fk_hand': jNames['hand'] + extraName  + '_1',
               'pole_vector': name + extraName + 'Pv',
               'ik_hand': jNames['hand'] + extraName + 'Ik',
               'limb_options': name + 'Switch' + extraName,
               'bend_shoulder': jNames['shoulder'] + 'Bend' + extraName,
               'bend_elbow': jNames['elbow'] + 'Point' + extraName,
               'bend_hand': jNames['hand'] + 'Bend' + extraName,
               'clav': jNames['clav'] + extraName + '_1'}
        return dic

    def combineName(self, name, increments='', objectType=None, vSide=None, hSide=None):
        result = name
        if increments is not '':
            result = result + '_' + increments

        if objectType is not None:
            result = result + '_' + objectType

        if vSide is not None:
            result = vSide + result

        if hSide is not None:
            result = hSide + result

        return result

conventions = {'default': BaseConvention,
               'TTRig': TTConvention,
               'Supa': SupaConvention}