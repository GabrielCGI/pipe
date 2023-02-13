import os
import re
from pymel.core import *


class Standin:
    def __init__(self, standin):
        self.__standin = standin
        self.__object_name = ""
        self.__standin_name = ""
        self.__versions = {}
        self.__active_variant = ""
        self.__active_version = None
        self.parse()

    # Retrieve all the datas of the standin
    def parse(self):
        # object name
        standin_trsf = self.__standin.getParent()
        trsf_name = standin_trsf.name()
        self.__object_name = trsf_name

        # standin name
        standin_file_path = self.__standin.dso.get()
        if not re.match(r".*\.ass", standin_file_path):
            return False
        standin_file_name_ext = os.path.basename(standin_file_path)
        standin_file_name = os.path.splitext(standin_file_name_ext)[0]
        self.__standin_name = re.sub("_" + standin_file_name.split('_')[-1], '', standin_file_name)

        # active variant and version
        path_version_dir = os.path.dirname(standin_file_path)
        path_variant_dir = os.path.dirname(path_version_dir)
        self.__publis_ass_dir = os.path.dirname(path_variant_dir)
        variant = os.path.basename(path_variant_dir)
        self.__active_variant = variant.split('_')[-1]
        self.__active_version = os.path.basename(path_version_dir)

        # variants and versions
        self.__versions.clear()
        path_asset_dir = os.path.dirname(path_variant_dir)
        for variant in os.listdir(path_asset_dir):
            variant_dir = path_asset_dir + "/" + variant
            if os.path.isdir(variant_dir):
                self.__versions[variant.split('_')[-1]] = []
                for version in os.listdir(variant_dir):
                    version_dir = variant_dir + "/" + version
                    if os.path.isdir(version_dir):
                        self.__versions[variant.split('_')[-1]].append((version, version_dir))

        for variant in self.__versions.keys():
            self.__versions[variant] = sorted(self.__versions[variant], reverse=True)
        return True

    # Getter of object name
    def get_object_name(self):
        return self.__object_name

    # Getter of standin name
    def get_standin_name(self):
        return self.__standin_name

    # Getter of the active variant
    def get_active_variant(self):
        return self.__active_variant

    # Getter of the active version
    def get_active_version(self):
        return self.__active_version

    # Getter of the variants and versions
    def get_versions(self):
        return self.__versions

    # Get the last version
    def last_version(self):
        return self.__versions[self.__active_variant][0][0]

    # Getter of whether the standin is up to date
    def is_up_to_date(self):
        return self.last_version() == self.__active_version

    # Set a new variant and version
    def set_active_variant_version(self, variant, version):
        if self.__active_variant != variant or self.__active_version != version:
            if len(variant) > 0 and len(version) > 0:
                version_file = self.__publis_ass_dir + "/" + self.__standin_name + "_" + variant + "/" + version + "/" + \
                               self.__standin_name + "_" + variant + ".ass"
                if os.path.isfile(version_file):
                    self.__standin.dso.set(version_file)
                    self.__active_variant = variant
                    self.__active_version = version

    # Update to last version of the current variant
    def update_to_last(self):
        self.set_active_variant_version(self.__active_variant, self.last_version())

    # Getter of whether the standin active variant is a SD
    def has_version_in_sd(self):
        return self.__get_version_replaced("HD", "SD") is not None

    # Getter of whether the standin active variant is a HD
    def has_version_in_hd(self):
        return self.__get_version_replaced("SD", "HD") is not None

    # Get the version to replace
    def __get_version_replaced(self, old_v, new_v):
        if new_v in self.__active_variant: return None
        variant = self.__active_variant.replace(old_v, new_v)
        if variant in self.__versions.keys():
            for version in self.__versions[variant]:
                if self.__active_version == version[0]:
                    return variant
        return None

    # Set to a SD variant
    def set_to_sd(self):
        variant = self.__get_version_replaced("HD", "SD")
        if variant is not None:
            self.set_active_variant_version(variant, self.__active_version)

    # Set to a HD variant
    def set_to_hd(self):
        variant = self.__get_version_replaced("SD", "HD")
        if variant is not None:
            self.set_active_variant_version(variant, self.__active_version)

    # Convert the standin to maya object
    def convert_to_maya(self):
        dso = self.__standin.dso.get()
        maya_path = dso.replace(".ass", ".ma")

        filename = os.path.basename(maya_path)
        name, ext = os.path.splitext(filename)
        name_space = name + "_00"
        namespace_for_creation = name_space.replace(".", "_")

        refNode = system.createReference(maya_path, namespace=namespace_for_creation)
        nodes = FileReference.nodes(refNode)
        transform = self.__standin.getParent()
        trsf_parent = transform.getParent()
        if trsf_parent:
            parent(nodes[0], trsf_parent)

        m = xform(transform, matrix=True, query=True)
        xform(nodes[0], matrix=m)

        transform.visibility.set(False)
