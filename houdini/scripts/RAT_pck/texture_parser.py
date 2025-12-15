
#region Imports

from pxr import UsdShade
from pathlib import Path
import hou
import sys
import os 
import glob

from dataclasses import dataclass , field

# thread libs
import subprocess
import queue
import multiprocessing

def import_qtpy():
    """
    Try to import qtpy from any prism install found in C:/ILLOGIC_APP/Prism.

    Returns:
        bool: True if the import path is found and False otherwise 
    """
    
    prism_qt_glob_pattern = "C:/ILLOGIC_APP/Prism/*/app/PythonLibs/*"

    found = False
    for path in glob.glob(prism_qt_glob_pattern):
        pyside_path = os.path.join(path, 'PySide')
        if os.path.exists(pyside_path):
            found = True
            break
    
    if not found:
        return False
    
    if pyside_path not in sys.path:
        sys.path.append(pyside_path)
    if path not in sys.path:
        sys.path.append(path)
    return True

if not import_qtpy():
    sys.exit(1)

try:
    from qtpy import QtCore
except ImportError as e:
    sys.exit(1)


#endregion

#TODO Clean all code + comment

#region Threads

class WorkerThread(QtCore.QThread):
    """
    Thread class, which takes textures from a queue and calls converts them
    Returns a signal when thread completed

    Slightly modified from this : https://github.com/jtomori/batch_textures_convert
    """

    inc_signal = QtCore.Signal()

    def __init__(self, task_queue, output_path, id):
        super(WorkerThread, self).__init__()

        self.queue = task_queue
        self.output_path = output_path
        self.id = id
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        reason = "finished"
        while not self._stop:
            try:
                texture_in = self.queue.get_nowait() # item if there is else empty

                # find output path
                if self.output_path : 
                    texture_out = os.path.join(self.output_path , os.path.basename(texture_in) + '.rat')
                else : 
                    texture_out = texture_in + '.rat'

                cmd = ["iconvert" , texture_in , texture_out]

                # idk what these mean
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                if cmd:
                    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, startupinfo=startupinfo)
                    out_bytes = p.communicate()[0] or b'' # i also dk what this means
                    try :
                        out = out_bytes.decode('utf-8', errors='replace')
                    except Exception : 
                        out = str(out_bytes)
                    
                    print ("\nThread #{}".format(self.id))
                    print ("Command: {}".format( " ".join(cmd) ))
                    print ("Command output:\n{dashes}\n{out}{dashes}".format(out=out, dashes="-"*50))
                    print ("Return code: {}\n".format(p.returncode))
                else:
                    print ("Cmd is None, skipping...")

                try : 
                    self.queue.task_done()
                except Exception : 
                    print("Task queue task error")
                    pass

                if not self._stop:
                    self.inc_signal.emit()

            except queue.Empty:
                reason = "empty queue"
                break

        if self.stop:
            reason = "stopped"

        print("Thread #{} finished ({})".format(self.id, reason))
        return

#endregion

#region Texture Parser

@dataclass
class TextureItem() : 
    name : str
    texture_paths : list[str] = field(default_factory=list)
    to_convert : list[str] = field(default_factory=list)

    def get_num_tex(self):
        return len(self.texture_paths)
    
    def get_num_toconv(self):
        return len(self.to_convert)
    
    def update_item(self) : 
        self.texture_paths = list(set(self.texture_paths))
        self.to_convert = list(set(self.to_convert))

# Some files have this in their houdini path to define the UV locations, but these do not exist in the real file. List is here to remove this.
TILE_ADDRESS_TOKENS = [".<UDIM>" , ".$F"]

class TextureParser():

    def __init__(self, ui = None):

        """
        Currently only works for Houdini when a node is selected, maybe expand its possible uses
        """

        self.ui = ui

        # Set a default number of threads according to our cpu
        self.cpu_threads_max = int(multiprocessing.cpu_count())
        self.cpu_threads_default = int(self.cpu_threads_max / 3)


        self.textures : list[TextureItem] = []

        self.texture_paths : list[str] = []
        self.files_to_convert : list[str] = []

        #This is only for Houdini
        # TODO : Make something to detect where we opened this, and handle opening from prism or houdini
        # if called_from == "houdini" or sum like dat

        self.current_node = None
        selected_nodes = hou.selectedNodes()

        if selected_nodes :  
            self.current_node = selected_nodes[0]

        self.find_textures_from_node(self.current_node)
        self.find_convert_files()

        for item in self.textures :
            item.update_item()

    #FIXME NEEDS URGENT CLEANING THIS IS UNREADABLE
    def find_textures_from_node(self, node):

        stage = node.stage()  # OR node.editableStage(), depending on use

        for prim in stage.Traverse():
            if prim.IsA(UsdShade.Shader):
                shader = UsdShade.Shader(prim)
                attr = shader.GetInput("file")
                if attr:
                    attr_str = str(attr.Get())[1:-1] # paths are contained in @dir1/dir2/test.jpg@ , this removes the @ @

                    # Remove the tile tokens if it has any
                    for token in TILE_ADDRESS_TOKENS : 
                        if token in attr_str :

                            #TODO : Handle non existant directories 

                            files_from_token = self.get_files_from_token(attr_str , token)
                            name = self.get_texture_name(attr_str)
                            self.texture_paths.extend(files_from_token)

                            texture_item = TextureItem(name, files_from_token, [])
                            #texture_item = self.create_item(name , files_from_token , [])

                            attr_str = ""
                    # 

                    if (not attr_str in self.texture_paths) and attr_str: 
                        self.texture_paths.append(attr_str)
                        name = self.get_texture_name(attr_str)

                        texture_item = TextureItem(name, attr_str, [])
                        #texture_item = self.create_item(name , attr_str , [])

                    if texture_item : 
                        self.textures.append(texture_item)

    #--------------------- Converter Methods ----------------------

    def find_convert_files(self):
        """
            Using texture paths, look for all their corresponding .rat files in the folder
            Basic parser 

            Output : List of files to convert
        """

        checked_dirs = []

        for i in range(len(self.textures)) :
            
            item = self.textures[i]
            files_to_convert = item.texture_paths.copy()

            for texture_path in item.texture_paths : 
                
                tex_dir_path = os.path.abspath(os.path.join(texture_path, os.pardir)) 

                if not tex_dir_path in checked_dirs : 

                    checked_dirs.append(tex_dir_path)

                    try :
                        dir_list = os.listdir(tex_dir_path)
                    except : 
                        print(f"Directory not found at {tex_dir_path}")
                        self.files_to_convert = None
                        return None
                
                for dir_file in dir_list :
                    for file in item.texture_paths :

                        rat = file + ".rat"

                        dir_path = Path(dir_file)
                        dir_file_path = Path(tex_dir_path) / dir_path

                        if dir_file_path == Path(rat) :
                            
                            if file in files_to_convert : 
                                files_to_convert.remove(file)

            item.to_convert = files_to_convert
            self.files_to_convert.extend(files_to_convert)

    def convert_to_rat(self, files_to_convert = None , threads = None,  path = None):
        """
            Converts a list of textures to .rat files, by calling workerthreads.  
            Saves them to the given path, if not specified saves them to the same path as the texture.
        """

        print("hello ? ")

        if files_to_convert :
            textures_list = files_to_convert 
        else : 
            textures_list = self.get_all_files_to_convert()

        if len(textures_list) <= 0 : 
            print("Rat conversion : we're done baby")
            if self.ui : 
                self.ui.conversion_progress.setMaximum(1)
                self.ui.conversion_progress.setValue(1)
            return

        if not textures_list:
            print("hell naw")
            return None

        if not threads : 
            threads = self.cpu_threads_default

        if not path : 
            path = os.path.abspath(os.path.join(textures_list[0], os.pardir)) 
        
        task_queue = queue.Queue()
        for tex in textures_list : 
            task_queue.put(tex)
        
        num_threads = min(threads, task_queue.qsize())

        workers = []
        for i in range(num_threads):
            proc = WorkerThread(task_queue, output_path=path , id = i)
            proc.start()
            workers.append(proc)

        task_queue.join()

        for w in workers:
            w.stop()

            if self.ui : 
                self.ui.conversion_progress_val += 1
                self.ui.conversion_progress.setValue(self.ui.conversion_progress_val)

            w.wait()

        print("Rat conversion : All workers finished")
    
    #---------------------------- Utils ------------------------------

    def get_texture_name(self, filepath):
        
        texture_name_str_replace = filepath.replace('\\' , '/')
        texture_name_str = texture_name_str_replace.split("/")[-1]        

        return texture_name_str

    def get_files_from_token(self, file_path_with_token , token):

        file_path_cleaned = file_path_with_token.replace(token , "*")

        files_from_token = []
        for file in glob.glob(file_path_cleaned):
            files_from_token.append(file)

        return files_from_token

    def get_all_texture_paths(self):
        textures = []
        for item in self.textures : 
            textures.extend(item.texture_paths)
        
        return list(set(textures))

    def get_all_files_to_convert(self):

        textures = []
        for item in self.textures : 
            textures.extend(item.to_convert)

        return list(set(textures))
    
    def get_all_names(self):

        names = []
        for item in self.textures : 
            names.append(item.name)

        return names

#endregion
#endregion