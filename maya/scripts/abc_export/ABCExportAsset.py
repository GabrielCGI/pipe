import os
import time
import logging
import pymel.core as pm

try:
    from common.utils import *
except:
    pass


class ABCExportAsset:

    @staticmethod
    def __optimize_scene_size():
        """
        Optimize Scene Size by cleaning it up
        :return:
        """
        print("\nvvvvvvvvvvvvvvvv Optimize Scene Size vvvvvvvvvvvvvvvv")
        pm.mel.source('cleanUpScene')
        pm.mel.scOpt_performOneCleanup({
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
        """
        Delete all unknown Nodes
        :return:
        """
        print("\nvvvvvvvvvvvvvvv Delete Unknown Nodes vvvvvvvvvvvvvvvv")
        unknown = pm.ls(type="unknown")
        if unknown:
            print("Removing:" + unknown)
            pm.delete(unknown)
        else:
            print("No unknown nodes found")
        print("^^^^^^^^^^^^^^^ Delete Unknown Nodes ^^^^^^^^^^^^^^^^\n")

    @staticmethod
    def __remove_unknown_plugins():
        """
        Remoave all unknown Plugins
        :return:
        """
        print("\nvvvvvvvvvvvvvv Remove Unknown Plugins vvvvvvvvvvvvvvv")
        old_plug = pm.unknownPlugin(query=True, list=True)
        if old_plug:
            for plug in old_plug:
                print("Removing:" + plug)
                try:
                    pm.unknownPlugin(plug, remove=True)
                except Exception as e:
                    print(e)
        else:
            print("No unknown plugin found")
        print("^^^^^^^^^^^^^^ Remove Unknown Plugins ^^^^^^^^^^^^^^^\n")

    @staticmethod
    def __unlock_all_nodes():
        """
        Unlock all Nodes
        :return:
        """
        print("\n------------------ Unlock All Nodes -----------------\n")
        all_nodes = pm.ls()
        if all_nodes:
            for node in all_nodes:
                pm.lockNode(node, l=False)

    @staticmethod
    def __remove_blast_panel_error():
        """
        Fix CgAbBlastPanel Error
        :return:
        """
        print("\n------------ Remove CgAbBlastPanel Error ------------\n")
        for model_panel in pm.getPanel(typ="modelPanel"):
            # Get callback of the model editor
            callback = pm.modelEditor(model_panel, query=True, editorChanged=True)
            # If the callback is the erroneous `CgAbBlastPanelOptChangeCallback`
            if callback == "CgAbBlastPanelOptChangeCallback":
                # Remove the callbacks from the editor
                pm.modelEditor(model_panel, edit=True, editorChanged="")
        if pm.objExists("uiConfigurationScriptNode"):
            pm.delete("uiConfigurationScriptNode")

    @staticmethod
    def __fix_isg():
        """
        Fix initialShadingGroup Error
        :return:
        """
        print("\n-------------- Fix initialShadingGroup --------------\n")
        pm.lockNode('initialShadingGroup', lock=0, lockUnpublished=0)
        pm.lockNode('initialParticleSE', lock=0, lockUnpublished=0)

    @staticmethod
    def next_version(folder):
        """
        Get the next version (version when the ABC will be exported)
        :param folder:
        :return:
        """
        version = 1
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if os.path.isdir(os.path.join(folder, f)):
                    try:
                        v = int(f)
                        if v > version:
                            version = v
                    except TypeError:
                        pass
        path = os.path.join(folder, str(version).zfill(4))
        while os.path.exists(path):
            version += 1
            path = os.path.join(folder, str(version).zfill(4))
        return version

    def __init__(self, name, namespace, geos):
        """
        Constructor
        :param name
        :param namespace
        :param geos
        """
        self.__name = name
        self.__namespace = namespace
        self.__num = 0
        self.__geos = geos

    def get_name(self):
        """
        Getter of the name
        :return:
        """
        return self.__name

    def get_name_with_num(self):
        """
        Getter of the name merged with the num
        :return: name with num
        """
        return self.__name + "_" + str(self.__num).zfill(2)

    def set_num(self, num):
        """
        Setter of the num
        :param num
        :return:
        """
        self.__num = num

    def get_geos(self):
        """
        Getter of the geos
        :return: geos
        """
        return self.__geos

    def export(self, folder, start, end, subsamples_enabled, subsamples, euler_filter):
        """
        Export this reference in ABC in a new version
        :param folder
        :param start
        :param end
        :param subsamples_enabled
        :param subsamples
        :param euler_filter
        :return:
        """
        abc_name = self.get_name_with_num()
        asset_dir_path = os.path.join(folder, abc_name)
        next_version = ABCExportAsset.next_version(asset_dir_path)
        version_dir_path = os.path.join(asset_dir_path, str(next_version).zfill(4))
        path = os.path.join(version_dir_path, abc_name + ".abc")
        path = path.replace("\\", "/")
        log_path = os.path.join(version_dir_path, "export_"+time.strftime("%d_%m_%Y")+".log")
        log_path = log_path.replace("\\", "/")

        command = "-frameRange %s %s -attrPrefix data" % (start, end)
        if subsamples_enabled:
            command += " -step 1.0"
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

        time_log = "Time    : " + time.strftime("%d-%m-%Y %H:%M:%S")

        os.makedirs(version_dir_path, exist_ok=True)
        pm.refresh(suspend=True)
        print(command)
        pm.AbcExport(j=command)
        pm.refresh(suspend=False)

        self.__export_light(version_dir_path, start, end)

        # Logs
        time_log += " --> " + time.strftime("%H:%M:%S")+"\n"
        char_log = "Char    : " + abc_name+"\n"
        version_log = "Version : " + str(next_version).zfill(4)+"\n"
        export_path_log = "Path    : " + path+"\n"
        scene_name = str(pm.sceneName())
        source_scene_log = "Scene   : " + scene_name if len(scene_name) > 0 else "untitled"+"\n"
        with open(log_path, "w") as log_file:
            log_file.write(time_log+export_path_log+char_log+version_log+source_scene_log)

    def __export_light(self, version_dir_path, start, end):
        """
        Export the lights of the Asset if it has some
        :param version_dir_path
        :param start
        :param end
        :return:
        """
        lights = pm.ls(self.__namespace + ":*", type="light")
        if len(lights) > 0:
            self.__optimize_scene_size()
            self.__delete_unknown_node()
            self.__remove_unknown_plugins()
            self.__unlock_all_nodes()
            self.__remove_blast_panel_error()
            self.__fix_isg()

            bake_list = []
            for n in lights:
                # Check if selected object is a child of an object
                par = pm.listRelatives(n, parent=True)
                if par is not None:
                    name_export = n.split(':')[-1].strip("Shape")
                    # Duplicate object
                    dupl_obj = pm.duplicate(n, name=name_export, rc=True, rr=True)

                    # Delete duplicated children
                    children_td = pm.listRelatives(dupl_obj, c=True, pa=True)[1:]
                    for c in children_td:
                        delete(c)

                    # Unparent object, Add constraints and append it to bake List
                    to_bake = pm.parent(dupl_obj, w=True)
                    bake_list.append(to_bake)
                    pm.parentConstraint(n, to_bake, mo=False)
                    pm.scaleConstraint(n, to_bake, mo=False)

            # Bake animation and delete constraints
            for i in bake_list:
                pm.bakeResults(i, t=(start, end))
                pm.delete(i[0], constraints=True)

            abc_name = self.get_name_with_num()
            path = os.path.join(version_dir_path, abc_name + "_light.abc")
            path = path.replace("\\", "/")
            pm.select(bake_list)
            pm.exportSelected(path, type="mayaAscii")

            for i in bake_list:
                pm.delete(i)
