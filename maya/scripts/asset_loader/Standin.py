import os
import re
import pymel.core as pm
from common.standin_utils import *

class Standin:
    def __init__(self, standin):
        """
        Constructor
        :param standin
        """
        self.__standin = standin
        self.__object_name = ""
        self.__standin_name = ""
        self.__versions = {}
        self.__active_variant = ""
        self.__active_version = None
        self.__parse_valid = False
        self.__parse()

    def __parse(self):
        """
        Retrieve all the datas of the standin
        :return:
        """
        # Use the parse_standin function in common package (Illogic package)
        parsed_data = parse_standin(self.__standin)
        self.__object_name = parsed_data["object_name"]
        self.__parse_valid = parsed_data["valid"]
        if self.__parse_valid:
            self.__standin_name = parsed_data["standin_name"]
            self.__publish_ass_dir = parsed_data["publish_ass_dir"]
            self.__active_variant = parsed_data["active_variant"]
            self.__active_version = parsed_data["active_version"]
            self.__versions = parsed_data["standin_versions"]

    def is_valid(self):
        """
        Getter of whether the StandIn is valid or not
        :return: i valid
        """
        return self.__parse_valid

    def get_object_name(self):
        """
        Getter of object name
        :return: object name
        """
        return self.__object_name

    def get_standin_name(self):
        """
        Getter of standin name
        :return: standin name
        """
        return self.__standin_name

    def get_active_variant(self):
        """
        Getter of the active variant
        :return: active variant
        """
        return self.__active_variant

    def get_active_version(self):
        """
        Getter of the active version
        :return: active version
        """
        return self.__active_version

    def get_versions(self):
        """
        Getter of the variants and versions
        :return: variants and versions
        """
        return self.__versions

    def last_version(self):
        """
        Get the last version
        :return: last version
        """
        return self.__versions[self.__active_variant][0][0]

    def is_up_to_date(self):
        """
        Getter of whether the standin is up to date
        :return: is up to date
        """
        return self.last_version() == self.__active_version

    def set_active_variant_version(self, variant, version):
        """
        Set a new variant and version
        :param variant
        :param version
        :return:
        """
        if self.__active_variant != variant or self.__active_version != version:
            if len(variant) > 0 and len(version) > 0:
                version_file = self.__publish_ass_dir + "/" + self.__standin_name + "_" + variant + "/" + version + "/" + \
                               self.__standin_name + "_" + variant + ".ass"
                if os.path.isfile(version_file):
                    self.__standin.dso.set(version_file)
                    self.__active_variant = variant
                    self.__active_version = version

    def update_to_last(self):
        """
        Update to last version of the current variant
        :return:
        """
        self.set_active_variant_version(self.__active_variant, self.last_version())

    def has_version_in_sd(self):
        """
        Getter of whether the standin active variant is a SD
        :return: has version in sd
        """
        return self.__get_version_replaced("HD", "SD") is not None

    def has_version_in_hd(self):
        """
        Getter of whether the standin active variant is a HD
        :return: has version in hd
        """
        return self.__get_version_replaced("SD", "HD") is not None

    def __get_version_replaced(self, old_v, new_v):
        """
        Get the version to replace
        :param old_v: old version
        :param new_v: new version
        :return: active variant
        """
        if new_v in self.__active_variant: return None
        variant = self.__active_variant.replace(old_v, new_v)
        if variant in self.__versions.keys():
            for version in self.__versions[variant]:
                if self.__active_version == version[0]:
                    return variant
        return None

    def set_to_sd(self):
        """
        Set to a SD variant
        :return:
        """
        variant = self.__get_version_replaced("HD", "SD")
        if variant is not None:
            self.set_active_variant_version(variant, self.__active_version)

    def set_to_hd(self):
        """
        Set to a HD variant
        :return:
        """
        variant = self.__get_version_replaced("SD", "HD")
        if variant is not None:
            self.set_active_variant_version(variant, self.__active_version)

    def convert_to_maya(self):
        """
        Convert the standin to maya object
        :return:
        """
        dso = self.__standin.dso.get()
        maya_path = dso.replace(".ass", ".ma")

        filename = os.path.basename(maya_path)
        name, ext = os.path.splitext(filename)
        name_space = name + "_00"
        namespace_for_creation = name_space.replace(".", "_")

        refNode = pm.system.createReference(maya_path, namespace=namespace_for_creation)
        nodes = pm.FileReference.nodes(refNode)
        transform = self.__standin.getParent()
        trsf_parent = transform.getParent()
        if trsf_parent:
            pm.group(nodes[0], parent=trsf_parent)

        m = pm.xform(transform, matrix=True, query=True)
        pm.xform(nodes[0], matrix=m)

        transform.visibility.set(False)
