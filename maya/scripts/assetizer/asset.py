
#TO DO ADD LOD AND VARIANT DROPDOWN


import os
import maya.cmds as cmds
from PySide2 import QtCore
from PySide2 import QtWidgets




class Variant():
    def __init__(self, name, variant_directory):
        self.name = name
        self.full_path = os.path.join(variant_directory,name)


class VariantSet():
    def __init__(self, name, variantSet_directory):
        self.name = name
        self.variantSet_directory = variantSet_directory
        self.all_variants = self.get_all_variants()

    def get_all_variants(self):
        all_variants = []
        list = os.listdir(self.variantSet_directory)
        for name in list:
            variant = Variant(name,self.variantSet_directory)
            all_variants.append(variant)
        return all_variants


class Asset():
    def __init__(self, maya_proxy_name):
        self.maya_proxy_name = maya_proxy_name
        self.dso = self.get_dso()
        self.ass_directory = self.get_ass_directory()
        self.current_variantName = self.get_current_variantName()
        self.current_variantSetName = self.get_current_variantSetName()
        self.all_variantSets = self.get_all_variantSets(self.ass_directory)
        #self.all_LOD = self.get_all_LOD()
        self.name = self.get_name()

    def get_all_variantSets(self, ass_directory):
        all_variantSets = []
        print (ass_directory)
        list = [ name for name in os.listdir(ass_directory) if os.path.isdir(os.path.join(ass_directory, name)) ]
        for name in list:
            variantSet_directory = os.path.join(ass_directory,name)
            variantSet = VariantSet(name, variantSet_directory)
            all_variantSets.append(variantSet)
        return all_variantSets


    def get_dso(self):
        value = cmds.getAttr(self.maya_proxy_name+".dso")
        return value

    def get_variantSet_by_name(self, variantSet_name):
        for variantSet in self.all_variantSets:
            if variantSet.name == variantSet_name:
                return variantSet



    def get_variant_by_name(self, variantSet_name, variant_name):
        variantSet = self.get_variantSet_by_name(variantSet_name)
        for variant in variantSet.all_variants:
            if variant.name == variant_name:
                return variant

    def get_ass_directory(self):
        ass_directory=  os.path.dirname(os.path.dirname(self.dso))
        return ass_directory

    def get_current_variantName(self):
        current_variant_name= self.dso.split("_")[-1]
        return current_variant_name

    def get_current_variantSetName(self):
        print ("get_current_variantSetName() result : ")
        basename = os.path.basename(self.dso)
        current_variantSet_name = basename.split("_")[-3]+"_"+ basename.split("_")[-2]
        return current_variantSet_name

    def get_name(self):
        name = self.dso.split("_")[0]
        return name
