import os
import logging
from pymel.core import *

try:
    from utils import *
except:
    pass


class ABCExportAsset:

    @staticmethod
    def __optimize_scene_size():
        print("\nvvvvvvvvvvvvvvvv Optimize Scene Size vvvvvvvvvvvvvvvv")
        mel.source('cleanUpScene')
        mel.scOpt_performOneCleanup({
            "nurbsSrfOption",
            "setsOption",
            "transformOption",
            "renderLayerOption",
            "renderLayerOption",
            "animationCurveOption",
            "groupIDnOption",
            "unusedSkinInfsOption",
            "groupIDnOption",
            "shaderOption",
            "ptConOption",
            "pbOption",
            "snapshotOption",
            "unitConversionOption",
            "referencedOption",
            "brushOption",
            "unknownNodesOption",
        })
        print("^^^^^^^^^^^^^^^^ Optimize Scene Size ^^^^^^^^^^^^^^^\n")

    @staticmethod
    def __delete_unknown_node():
        print("\nvvvvvvvvvvvvvvv Delete Unknown Nodes vvvvvvvvvvvvvvvv")
        unknown = ls(type="unknown")
        if unknown:
            print("Removing:" + unknown)
            delete(unknown)
        else:
            print("No unknown nodes found")
        print("^^^^^^^^^^^^^^^ Delete Unknown Nodes ^^^^^^^^^^^^^^^^\n")

    @staticmethod
    def __remove_unknown_plugins():
        print("\nvvvvvvvvvvvvvv Remove Unknown Plugins vvvvvvvvvvvvvvv")
        old_plug = cmds.unknownPlugin(query=True, list=True)
        if old_plug:
            for plug in old_plug:
                print("Removing:" + plug)
                try:
                    cmds.unknownPlugin(plug, remove=True)
                except Exception as e:
                    print(e)
        else:
            print("No unknown plugin found")
        print("^^^^^^^^^^^^^^ Remove Unknown Plugins ^^^^^^^^^^^^^^^\n")

    @staticmethod
    def __unlock_all_nodes():
        print("\n------------------ Unlock All Nodes -----------------\n")
        all_nodes = ls()
        if all_nodes:
            for node in all_nodes:
                lockNode(node, l=False)

    @staticmethod
    def __remove_blast_panel_error():
        print("\n------------ Remove CgAbBlastPanel Error ------------\n")
        for model_panel in getPanel(typ="modelPanel"):
            # Get callback of the model editor
            callback = modelEditor(model_panel, query=True, editorChanged=True)
            # If the callback is the erroneous `CgAbBlastPanelOptChangeCallback`
            if callback == "CgAbBlastPanelOptChangeCallback":
                # Remove the callbacks from the editor
                modelEditor(model_panel, edit=True, editorChanged="")
        if objExists("uiConfigurationScriptNode"):
            delete("uiConfigurationScriptNode")

    @staticmethod
    def __fix_isg():
        print("\n-------------- Fix initialShadingGroup --------------\n")
        lockNode('initialShadingGroup', lock=0, lockUnpublished=0)
        lockNode('initialParticleSE', lock=0, lockUnpublished=0)

    # Get the next version (version when the ABC will be exported)
    @staticmethod
    def next_version(folder):
        version = 1
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if os.path.isdir(os.path.join(folder, f)):
                    try:
                        v = int(f)
                        if v > version:
                            version = v
                    except Typeerror:
                        pass
        path = os.path.join(folder, str(version).zfill(4))
        while os.path.exists(path):
            version += 1
            path = os.path.join(folder, str(version).zfill(4))
        return version

    def __init__(self, name, namespace, geos):
        self.__name = name
        self.__namespace = namespace
        self.__num = 0
        self.__geos = geos

    # Getter of the name
    def get_name(self):
        return self.__name

    # Getter of the name merged with the num
    def get_name_with_num(self):
        return self.__name + "_" + str(self.__num).zfill(2)

    # Setter of the num
    def set_num(self, num):
        self.__num = num

    # Getter of the geos
    def get_geos(self):
        return self.__geos

    # Export this reference in ABC in a new version
    def export(self, folder, start, end, subsamples_enabled, subsamples, euler_filter):
        self.__optimize_scene_size()
        self.__delete_unknown_node()
        self.__remove_unknown_plugins()
        self.__unlock_all_nodes()
        self.__remove_blast_panel_error()
        self.__fix_isg()

        abc_name = self.get_name_with_num()
        asset_dir_path = os.path.join(folder, abc_name)
        next_version = ABCExportAsset.next_version(asset_dir_path)
        version_dir_path = os.path.join(asset_dir_path, str(next_version).zfill(4))
        path = os.path.join(version_dir_path, abc_name + ".abc")
        path = path.replace("\\", "/")

        os.makedirs(version_dir_path, exist_ok=True)

        command = "-frameRange %s %s" % (start, end)
        if subsamples_enabled:
            command +=" -step 1.0"
            for frame in subsamples.split(" "):
                command += " -frameRelativeSample " + frame

        command += " -writeVisibility  -stripNamespaces  -worldSpace -dataFormat ogawa"
        if euler_filter:
            command += " -eulerFilter"
        if not self.__geos:
            return

        for geo in self.__geos:
            command += " -root %s" % geo
        command += " -file \"%s\"" % (path)

        refresh(suspend=True)
        AbcExport(j=command)
        refresh(suspend=False)

        self.__export_light(version_dir_path, start, end)

    def __export_light(self, version_dir_path, start, end):
        lights = ls(self.__namespace + ":*", type="light")
        if len(lights) > 0:
            bake_list = []
            for n in lights:
                # Check if selected object is a child of an object
                par = listRelatives(n, parent=True)
                if par is not None:
                    name_export = n.split(':')[-1].strip("Shape")
                    # Duplicate object
                    dupl_obj = duplicate(n, name=name_export, rc=True, rr=True)

                    # Delete duplicated children
                    children_td = listRelatives(dupl_obj, c=True, pa=True)[1:]
                    for c in children_td:
                        delete(c)

                    # Unparent object, Add constraints and append it to bake List
                    to_bake = parent(dupl_obj, w=True)
                    bake_list.append(to_bake)
                    parentConstraint(n, to_bake, mo=False)
                    scaleConstraint(n, to_bake, mo=False)

            # Bake animation and delete constraints
            for i in bake_list:
                bakeResults(i, t=(start, end))
                delete(i[0], constraints=True)

            abc_name = self.get_name_with_num()
            path = os.path.join(version_dir_path, abc_name + "_light.abc")
            path = path.replace("\\", "/")
            select(bake_list)
            exportSelected(path, type="mayaAscii")

            for i in bake_list:
                delete(i)
