import shutil
import os
import threading
import re
import time
import datetime
import json
from json import JSONEncoder
import subprocess
from queue import Queue
import sys

from arnold import *

from common.utils import *

try:
    import pymel.all as pm
except:
    # Maya not found
    pass

# ######################################################################################################################

_RANCH_CACHE_FOLDER = "I:/ranch/ranch_cache2"
_LOGS_FOLDER = "I:/ranch/logs"
_MAX_NB_THREADs = 16

_ASS_PATHS_FILE_EXTENSION = "paths"

_RELATIVE_SEARCH_DISK = ["I:/", "B:/", "R:/"]

# ######################################################################################################################

# 18 + Length of longer message possible (here : "File already exists")
_LENGTH_PADDING = 18 + 19
_LENGTH_HEADER_FOOTER = 200


class CollectorCopier:

    # Generate the dict data for a path
    @staticmethod
    def __generate_data_for_path(path):
        match = re.match(r"^([A-Z]):[\\/](.*)$", path)
        if match:
            disk_letter = match.group(1)
            path_without_disk_letter = match.group(2)
            destination = os.path.join(_RANCH_CACHE_FOLDER, disk_letter, path_without_disk_letter)
            return {
                "src": path.replace("\\", "/"),
                "dest": destination,
                "folder_dest": os.path.dirname(destination),
                "size": os.path.getsize(path)
            }
        return None

    def __init__(self, force_override_ass_paths_files=False):
        self.__datas = []
        self.__force_override_ass_paths_files = force_override_ass_paths_files
        self.__scene_path = ""
        self.__log_file_name = ""
        self.__log_file = None
        self.__data_file_name = ""
        self.__reinit_copy_attributes()
        self.__datas_lock = threading.Lock()
        self.__progress_lock = threading.Lock()
        self.__output_queue = Queue()
        self.__output_enabled = False

    def __to_str_past_time(self, time_start, time_end):
        return time.strftime("%H:%M:%S", time.gmtime(time_end - time_start))

    # Init some attributes for the copy and logs
    def __reinit_copy_attributes(self):
        self.__total_file_size = 0
        self.__current_file_size = 0
        self.__total_file_nb = 0
        self.__current_file_nb = 1
        self.__current_data_index = 0
        self.__datas_length = len(self.__datas)
        self.__max_length_path = 0

    # Save datas during the collect phase
    def __store_datas(self):
        collector_copier_dict = {
            "datas": self.__datas,
            "scene_path": self.__scene_path,
            "file_logs_name": self.__log_file_name
        }
        json_dict = json.dumps(collector_copier_dict)
        f = open(self.__data_file_name, "w")
        f.write(json_dict)
        f.close()

    # Retrieve datas during the copy phase saved during the collect phase
    def __retrieve_datas(self, file_data_path):
        self.__data_file_name = file_data_path
        f = open(self.__data_file_name, "r")
        json_dict = f.read()
        f.close()
        os.remove(self.__data_file_name)
        collector_copier_dict = json.loads(json_dict)
        self.__datas = collector_copier_dict["datas"] if "datas" in collector_copier_dict else []
        self.__scene_path = collector_copier_dict["scene_path"] if "scene_path" in collector_copier_dict else ""
        self.__log_file_name = collector_copier_dict[
            "file_logs_name"] if "file_logs_name" in collector_copier_dict else ""
        self.__reinit_copy_attributes()

    # Output informations (write into logs and print in console)
    def __output(self, msg, print_msg=True):
        self.__log_file.write(msg + "\n")
        self.__log_file.flush()
        if print_msg:
            print(msg, flush=True)

    # Output the logs in a file and text thanks to a message queue
    def __thread_output(self):
        while self.__output_enabled or not self.__output_queue.empty():
            if not self.__output_queue.empty():
                msg = self.__output_queue.get_nowait()
                self.__output(msg, False)
            else:
                # Allow most important threads to work before checking if a message is available
                time.sleep(0.5)

    # #################################################### COLLECT #####################################################
    def __get_paths_with_udim(self, path):
        paths = []
        folder, filename = os.path.split(path)
        if not os.path.exists(folder):
            return []

        match_udim = re.match(r"^(.*)(?:<udim>|[0-9]{4})(.*)$", filename)
        if match_udim:
            start = match_udim.group(1)
            ext = match_udim.group(2)
            if os.path.exists(folder):
                for file in os.listdir(folder):
                    match_udim = re.match(r"^" + start + r"[0-9]{4}" + ext + r"$", file)
                    if match_udim:
                        paths.append(os.path.join(folder, file))
            return paths if len(paths) > 0 else []
        else:
            return [path] if os.path.exists(path) else []

    # Retrieve the paths dependent of a path (can be relative or absolute and an UDIM)
    # Check the UDIMS and if the path is relative
    def __retrieve_dependent_paths(self, path, check_relative_path=True):
        paths = []
        folder = os.path.dirname(path)
        if os.path.exists(folder):
            # Get all the paths if udim or only the current path
            paths_found = self.__get_paths_with_udim(path)
            for path in paths_found:
                if path not in paths:
                    paths.append(path)
        else:
            if check_relative_path:
                for disk in _RELATIVE_SEARCH_DISK:
                    path_with_disk = os.path.join(disk, path)
                    paths_found = self.__retrieve_dependent_paths(path_with_disk, False)
                    if len(paths_found) > 0:
                        paths = paths_found
                        break
        return paths

    # Retrieve all the paths used in Maya Scene
    def __retrieve_paths_in_maya(self):
        time_start = time.time()
        self.__output("\n+- Start retrieve all the paths in Maya -----")
        count_path = 1
        # Get FileNodes, AiImages, AiStandins and References
        list_files = pm.ls(type="file")
        list_images = pm.ls(type="aiImage")
        list_standins = pm.ls(type='aiStandIn')
        list_refs = pm.ls(references=True)
        nb_tot = len(list_files) + len(list_images) + len(list_standins) + len(list_refs)
        paths = []
        # FILES
        if len(list_files) > 0: self.__output("| ----- Retrieve paths in FileNodes")
        for file in list_files:
            path = file.fileTextureName.get()
            filenode_paths = self.__retrieve_dependent_paths(path)
            if len(filenode_paths)==0:
                self.__output("| " + str(count_path) + "/" + str(nb_tot) +
                              " - Error FileNode texture path do not exists : " + path)
            for fn_path in filenode_paths:
                self.__output("| " + str(count_path) + "/" + str(nb_tot) + " - FileNode texture path found : " + fn_path)
                paths.append(fn_path)
            count_path += 1
        # IMAGES
        if len(list_images) > 0: self.__output("| ----- Retrieve paths in Images")
        for image in list_images:
            path = image.filename.get()
            image_paths = self.__retrieve_dependent_paths(path)
            if len(image_paths)==0:
                self.__output("| " + str(count_path) + "/" + str(nb_tot) +
                              " - Error Image path do not exists : " + path)
            for img_path in image_paths:
                self.__output("| " + str(count_path) + "/" + str(nb_tot) + " - Image path found : " + img_path)
                paths.append(img_path)
            count_path += 1
        # STANDINS
        if len(list_standins) > 0: self.__output("| ----- Retrieve paths in StandIns")
        for standin in list_standins:
            path = standin.dso.get()
            standin_paths = self.__retrieve_dependent_paths(path)
            if len(standin_paths)==0:
                self.__output("| " + str(count_path) + "/" + str(nb_tot) +
                              " - Error StandIn dso do not exists : " + path)
            for sdin_path in standin_paths:
                self.__output("| " + str(count_path) + "/" + str(nb_tot) + " - StandIn dso found : " + sdin_path)
                paths.append(sdin_path)
            count_path += 1
        # REFERENCES
        if len(list_refs) > 0: self.__output("| ----- Retrieve paths in References")
        for ref in list_refs:
            try:
                path = pm.referenceQuery(ref, filename=True)
            except Exception:
                self.__output("| " + str(count_path) + "/" + str(nb_tot) +
                              " - Error Reference node not associated to reference file : " + ref)
                continue
            reference_paths = self.__retrieve_dependent_paths(path)
            if len(reference_paths)==0:
                self.__output("| " + str(count_path) + "/" + str(nb_tot) +
                              " - Error Reference path do not exists : " + path)
            for ref_path in reference_paths:
                self.__output("| " + str(count_path) + "/" + str(nb_tot) + " - Reference path found : " + ref_path)
                paths.append(ref_path)
            count_path += 1

        # Add to the datas
        nb_added = 0
        for path in paths:
            if path not in self.__datas:
                nb_added += 1
                self.__datas.append(path)

        self.__output("+- End retrieve all the paths in Maya [" + str(nb_added) + "] ----- " +
                      self.__to_str_past_time(time_start, time.time()) + " -----")

    # Retrieve all paths in the ass files
    def __retrieve_ass_paths(self):
        time_start = time.time()
        self.__output("\n+- Start retrieve all the paths in ASS files -----")
        list_standin = pm.ls(type='aiStandIn')
        list_include_graph = pm.ls(type='aiIncludeGraph')
        ass_paths_count = 0
        i = 1
        ass_files = []
        pre_ass_files = []
        ass_regexp = r"^.*\.ass$"
        # Standin
        for standin in list_standin:
            ass_file = standin.dso.get()
            abc_layer = standin.abc_layers.get()
            if ass_file is not None and len(ass_file) > 0:
                pre_ass_files.append(ass_file)
            if abc_layer is not None and len(abc_layer) > 0:
                pre_ass_files.append(abc_layer)
        # Include Graph
        for include_graph in list_include_graph:
            ass_file = include_graph.filename.get()
            if ass_file is not None and len(ass_file) > 0:
                pre_ass_files.append(ass_file)

        for pre_ass_file in pre_ass_files:
            if pre_ass_file not in ass_files and re.match(ass_regexp, pre_ass_file) and os.path.exists(pre_ass_file):
                ass_files.append(pre_ass_file)

        nb_ass_files = len(ass_files)
        # Iterate through StandIn
        for ass_file in ass_files:
            ass_paths = []
            relative_paths = []
            texture_search_paths = []
            match = re.match(r"^(.*)\.\w*$", os.path.basename(ass_file))
            paths_info_filepath = os.path.join(os.path.dirname(ass_file),
                                               match.group(1) + "." + _ASS_PATHS_FILE_EXTENSION)

            paths_info_file_exits = os.path.exists(paths_info_filepath)

            str_ass_count = str(i) + "/" + str(nb_ass_files)
            # If the path file already exists we just retrieve the datas it contains instead of searching for it
            if paths_info_file_exits and not self.__force_override_ass_paths_files:
                self.__output(
                    "| " + str_ass_count + " - Paths info already exists for " + ass_file)
                path_info_file = open(paths_info_filepath, "r")
                ass_paths = json.loads(path_info_file.read())
                if len(ass_paths) > 0:
                    self.__output("\n".join(["|    +----> " + path for path in ass_paths]))
            else:
                # If the path file does not exists or if we want to force its creation we search for all the paths
                # in the .ass file
                if paths_info_file_exits:
                    open(paths_info_filepath, "w").close()

                path_info_file = open(paths_info_filepath, "a")

                self.__output("| " + str_ass_count + " - Search in " + ass_file)

                # Open the file and read its contents
                with open(ass_file, 'r') as f:
                    contents = f.read()

                # Define a regular expression pattern to match filenames with paths
                pattern = r'filename\s+\"([^\"]+)\"'
                pattern_option = r'texture_searchpath\s+\"([^\"]+)\"'
                # Find all filenames with paths that match the pattern
                matches = re.findall(pattern, contents)
                options = re.findall(pattern_option, contents)
                if len(options) > 0:
                    texture_search_paths = options[0].split(";")
                for match in matches:
                    if os.path.exists(match) and match not in ass_paths:
                        ass_paths.append(match)
                        self.__output("|    +----> " + match)
                    else:
                        udim_paths = self.__retrieve_dependent_paths(match)
                        if len(udim_paths) > 0:
                            for udim_path in udim_paths:
                                if os.path.exists(udim_path) and udim_path not in ass_paths:
                                    ass_paths.append(udim_path)
                                    self.__output("|    +----> " + udim_path)
                                else:
                                    relative_paths.extend(udim_paths)
                        else:
                            relative_paths.append(match)

                if len(relative_paths) > 0:
                    if len(texture_search_paths) == 0:
                        texture_search_paths = _RELATIVE_SEARCH_DISK

                    for base_path in texture_search_paths:
                        # If all file processed stop the search
                        if len(relative_paths) == 0:
                            break

                        # Try to find if the path is a reference to an env var
                        match = re.match(r"^\[(\w+)]$", base_path)
                        if match:
                            env_var_name = match.group(1)
                            env_var = os.getenv(env_var_name)
                            if env_var:
                                base_path = env_var

                        # For each file try to base_path, If exists remove the file from the list to processed
                        rel_path_to_remove = []
                        for rel_path in relative_paths:
                            absolute_path = os.path.join(base_path, rel_path)
                            if os.path.exists(absolute_path):
                                if absolute_path not in ass_paths:
                                    ass_paths.append(absolute_path)
                                self.__output("|    +----> " + absolute_path)
                                rel_path_to_remove.append(rel_path)
                        if len(rel_path_to_remove) > 0:
                            for rel_path in rel_path_to_remove:
                                relative_paths.remove(rel_path)

                path_info_file.write(json.dumps(ass_paths))
                path_info_file.close()

            path_info_file = open(paths_info_filepath, "r")
            ass_paths = json.loads(path_info_file.read())
            for ass_path in ass_paths:
                if ass_path not in self.__datas:
                    self.__datas.append(ass_path)
                    ass_paths_count += 1

            i += 1

        self.__output("+- End retrieve all the paths in ASS files [" + str(ass_paths_count) + "] ----- " +
                      self.__to_str_past_time(time_start, time.time()) + " -----")

    # ###################################################### COPY ######################################################

    # Copy with datas to Ranch
    def __copy_from_data(self, data):
        path_src = data["src"]
        path_dest = data["dest"]
        size_src = data["size"]
        count_file_str_length = 2 * len(str(self.__datas_length)) + 1
        str_length = self.__max_length_path + count_file_str_length + _LENGTH_PADDING
        try:
            os.makedirs(data['folder_dest'], exist_ok=True)

            # Check whether the file need to by copied
            do_copy = True
            if os.path.exists(path_dest):
                mtime_src = os.path.getmtime(path_src)
                mtime_dest = os.path.getmtime(path_dest)
                size_dest = os.path.getsize(path_dest)
                if mtime_src == mtime_dest and size_dest == size_src:
                    do_copy = False

            if do_copy:
                # Copy
                shutil.copy2(path_src, path_dest)

            # Output Logs
            with self.__progress_lock:
                self.__current_file_size += size_src
                percent_copied = round(self.__current_file_size / self.__total_file_size * 100, 2)
                str_percent = str(percent_copied).rjust(5) + "%"
                str_file_count = (str(self.__current_file_nb) + "/" + str(self.__total_file_nb)).rjust(
                    count_file_str_length)
                msg = "Copy On RANCH of" if do_copy else "File already exists"
                complete_msg = "| " + str_percent + " - " + str_file_count + " - " + msg + " : " + path_src + " "
                self.__output_queue.put(complete_msg.ljust(str_length, " ") + "|")
                self.__current_file_nb += 1
        except Exception as e:
            # Error while copying
            with self.__progress_lock:
                msg = "| error while copying " + path_src + " : " + str(e)
                self.__output_queue.put(msg.ljust(str_length, " ") + "|")

    # Thread of copy : It takes the data of the current file and copy it. It then take the next available
    def __thread_copy_file(self):
        file_available = True
        while file_available:
            # Increment current data Index
            with self.__datas_lock:
                index_data = self.__current_data_index
                self.__current_data_index += 1
            # Stop iterating through data if end reached
            if self.__current_data_index > self.__datas_length:
                file_available = False
            else:
                file_datas = self.__datas[index_data]
                # Copy the current file
                self.__copy_from_data(file_datas)

    # Copy all the files retrieved
    def __copy(self):
        time_start = time.time()

        # Sort the files according to their size to be more efficient.
        # Ex :
        # Thread1 ------------------- | ------------ | --------
        # Thread2 --------------- | ----------- | ------- | ---
        # Thread3 ------------- | --------- | ------ | ---- | -
        #                Better than :
        # Thread1 - | ------ | --------- | -------------
        # Thread2 --- | ------- | ----------- | ---------------
        # Thread3 ---- | -------- | ------------ | -------------------
        self.__datas.sort(key=lambda x: x.get("size"), reverse=True)

        # Init datas and copy attributes
        self.__reinit_copy_attributes()
        self.__total_file_nb = len(self.__datas)
        for data_copy in self.__datas:
            self.__total_file_size += data_copy["size"]
            self.__max_length_path = max(self.__max_length_path, len(data_copy["src"]))
        threads = []

        count_file_str_length = 2 * len(str(self.__datas_length)) + 1

        # Compute the good number of threads
        nb_thread = min(self.__total_file_nb, _MAX_NB_THREADs)

        # Start All Threads
        with self.__progress_lock:
            msg = "+- Copy On RANCH : " + str(nb_thread) + " threads launched for " + str(
                self.__total_file_nb) + " file(s) "

            self.__output_queue.put(
                "\n" + msg.ljust(self.__max_length_path + count_file_str_length + _LENGTH_PADDING, "-") + "+")
        for i in range(nb_thread):
            th = threading.Thread(target=self.__thread_copy_file)
            threads.append(th)
            th.start()
        # Join All Threads
        for th in threads:
            th.join()

        with self.__progress_lock:
            msg = "+- Copy On RANCH Finished ----- " + \
                  self.__to_str_past_time(time_start, time.time())

            self.__output_queue.put(
                msg.ljust(self.__max_length_path + count_file_str_length + _LENGTH_PADDING, "-") + "+")

    # Start the thread for writing in log file during copy
    def __start_thread_log(self):
        self.__output_enabled = True
        self.__thread_output = threading.Thread(target=self.__thread_output)
        self.__thread_output.start()

    # Stop the log thread
    def __stop_thread_log(self):
        self.__output_enabled = False
        self.__thread_output.join()

    # ##################################################### COMMON #####################################################
    def __generate_log_data(self):
        scene_dirname, scene_basename = os.path.split(self.__scene_path)
        match_name = re.match(r"^(.*)\.(?:ma|mb)$", scene_basename)
        scene_name = match_name.group(1)
        match_dir = re.match(r"^[A-Z]:[\\/](\w*)[\\/].*$", scene_dirname)
        project = match_dir.group(1)
        folder = os.path.join(_LOGS_FOLDER, project)
        os.makedirs(folder, exist_ok=True)
        name_file = os.path.join(folder, time.strftime("%Y_%m_%d_%H%M%S") + "_" + scene_name)
        self.__log_file_name = name_file + ".log"
        self.__data_file_name = name_file + ".data"

    # Create and start appending in the log file
    def __start_log(self):
        self.__log_file = open(self.__log_file_name, "a")

    # Close the log file
    def __stop_log(self):
        self.__log_file.close()

    # Generate the logs file name and the Header
    def __header_log(self):
        padding_length = (_LENGTH_HEADER_FOOTER - 21) // 2
        header = padding_length * "#" + " " + time.strftime("%Y-%m-%d %H:%M:%S") + " " + padding_length * "#"
        self.__output(header, False)

    # Generate the Footer
    def __footer_log(self):
        footer = _LENGTH_HEADER_FOOTER * "#"
        self.__output_queue.put(footer, False)

    # Generate all the datas from the file path
    def __generate_ranged_cache_dest(self):
        ranged_cache_paths = []
        for path in self.__datas:
            data = CollectorCopier.__generate_data_for_path(path)
            if data is not None:
                ranged_cache_paths.append(data)
        self.__datas = ranged_cache_paths

    # ###################################################### RUN #######################################################

    # Run Collector and Copier to Ranch
    def run_collect(self):
        self.__datas.clear()
        self.__scene_path = pm.sceneName()

        if len(self.__scene_path) == 0:
            print("----- SCENE NOT FOUND -----")
            return

        self.__generate_log_data()

        self.__start_log()

        self.__header_log()

        # MAYA PATHS
        self.__retrieve_paths_in_maya()
        # ASS PATHS
        self.__retrieve_ass_paths()

        # COPY
        self.__store_datas()
        dirname = os.path.dirname(__file__)
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen(["python", os.path.join(dirname, "copy_to_distant.py"), self.__data_file_name], startupinfo=si)

        self.__stop_log()

    def run_copy(self, file_data_path):
        self.__retrieve_datas(file_data_path)
        self.__start_log()
        self.__start_thread_log()
        self.__generate_ranged_cache_dest()
        self.__copy()
        self.__footer_log()
        self.__stop_thread_log()
        self.__stop_log()
