import nuke
import re
import os
from common.utils import *

class NukeScanner:
    def __init__(self):
        self.__files = []
        self.__folders = []
        self.__retrieve_shot()
        self.__retrieve_files()

    def __retrieve_shot(self):
        # I:\battlestar_2206\shots\longform_shot020\compo\shot020_comp0_01.nk
        self.__compo_filepath = nuke.root()['name'].value()
        match = re.match(r"^(.+)\\compo\\\w*\.nk$$",self.__compo_filepath)
        if match:
            self.__shot_dir = match.group(1).replace("\\","/")
        else:
            self.__shot_dir = None
        # TODO remove
        self.__shot_dir = r"I:/battlestar_2206/shots/longform_shot020"

    def __retrieve_files(self):
        read_nodes = nuke.allNodes("Read")
        for node in read_nodes:
            file_path = node["file"].value()
            # Test if in render_out
            if not file_path.startswith(self.__shot_dir):
                continue
            folder = os.path.dirname(file_path)
            if folder in self.__folders:
                continue
            self.__folders.append(folder)

    def __check_folder_recursive(self, folder):
        sub_used_folders = []
        sub_not_used_folders = []
        sub_used = False
        if not used:
            for child in os.listdir(folder):
                path = os.path.join(folder, child)
                if not os.path.isdir(path):
                    continue
                sub_folder_used = self.__check_folder_recursive(path)
                sub_used = sub_used or sub_folder_used
                if sub_folder_used:
                    sub_used_folders.append(path)
                else:
                    sub_not_used_folders.append(path)

        if not used:
            for sub_folder in sub_used_folders:
                self.__check_folder_recursive(sub_folder)
            if len(sub_used_folders) == 0:
                print(folder)
                return True
        return False

    def run(self):
        self.__check_folder_recursive(self.__shot_dir+"/render_out")
