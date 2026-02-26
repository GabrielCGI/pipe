
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
    finished_signal = QtCore.Signal(int)

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
        self.finished_signal.emit(self.id)
        return

#endregion

#region Texture Parser

@dataclass
class TextureItemInterface():
    name : str = field(default_factory=str)
    texture_path : str = field(default_factory=str)
    nodes : list[str] = field(default_factory=list)
    to_convert : int = field(default_factory=int)

    def get_num_tex(self):
        pass
    
    def get_num_toconv(self):
        pass

    def get_children(self):
        return []

    def get_textures_paths(self):
        pass

    def get_convert_paths(self):
        pass
    
    def compute_convert(self):
        pass 

    def update_item(self) : 
        pass

@dataclass
class TextureFile(TextureItemInterface):
    def get_attributes(self):
        attributes = {
            "Name" : self.name,
            "Path" : self.texture_path,
            "Nodes" : self.nodes,
            "Status" : self.to_convert
        }
        return attributes
    
    def get_num_tex(self):
        return 1
    
    def get_num_toconv(self):
        return self.to_convert
    
    def get_textures_paths(self):
        return [self.texture_path]
    
    def get_convert_paths(self):
        paths = []
        if self.to_convert : 
            paths.append(self.texture_path)    
        return paths

    def update_item(self) : 
        self.nodes = list(set(self.nodes))

@dataclass
class TextureFrames(TextureItemInterface) : 

    children : list[TextureItemInterface] = field(default_factory=list)

    def get_attributes(self):
        attributes = {
            "Name" : self.name,
            "Path" : "",
            "Nodes" : self.nodes,
            "Status" : self.to_convert,
            "Children" : self.children
        }
        return attributes

    def get_num_tex(self):
        return len(self.children)
    
    def get_num_toconv(self):
        return self.to_convert
    
    def get_textures_paths(self):
        paths = []
        for texture_item in self.children : 
            paths.append(texture_item.texture_path)
        return paths
    
    def get_convert_paths(self):
        paths = []
        for texture_item in self.children :
            if texture_item.to_convert : 
                paths.append(texture_item.texture_path)
        return paths

    def get_children(self):
        return self.children
    
    def compute_convert(self):
        nb_convert = 0
        for item in self.children :
            nb_convert += item.to_convert   
        self.to_convert = nb_convert

    def update_item(self) : 
        self.nodes = list(set(self.nodes))
        # self.children = list(set(self.children))
        self.compute_convert()

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

        self.texture_items : list[TextureItemInterface] = []
        self.texture_paths : list[str] = []
        self.files_to_convert : list[str] = []

        self.accepted_nodes : list[str] = ["materiallibrary"]

        for item in self.texture_items :
            item.update_item()

    def clear(self):

        self.texture_items.clear()
        self.texture_paths.clear()
        self.files_to_convert.clear()


    def find_textures_from_scene(self):
        """Find all nodes in a scene, and then all textures in those nodes.

        Raises:
            Exception: If not in solaris, stage does not exist causing an error
        """

        self.clear()

        main_stage = hou.node("/stage")
        if not main_stage : 
            raise Exception("")
        
        for node in main_stage.children() : 
            node_type = node.type().name()
            if node_type in self.accepted_nodes : 
                print(f"node_ytpe : {node_type} , accepted nodes : {self.accepted_nodes}")
                self.find_textures_from_node(node)
        
    def find_textures_from_node(self, node):


        stage = node.stage()  # OR node.editableStage(), depending on use
        node_name = node.name()

        if not stage : 
            return

        for prim in stage.Traverse():
            if not prim.IsA(UsdShade.Shader):
                continue

            shader = UsdShade.Shader(prim)
            attr = shader.GetInput("file") 

            if not attr:
                continue
            
            attr_str = str(attr.Get())[1:-1] # paths are contained in @dir1/dir2/test.jpg@ , this removes the @ @
            name = self.get_texture_name(attr_str)

            exists = False
            for item in self.texture_items : 
                if name == item.name :
                    exists = True
                    item.nodes.append(node_name)
                    item.update_item()
                    break

            texture_item = None
            # Remove the tile tokens if it has any (eg. UDIM)
            for token in TILE_ADDRESS_TOKENS : 
                if token in attr_str :

                    files_from_token = self.get_files_from_token(attr_str , token)
                    self.texture_paths.extend(files_from_token)

                    textures_from_token = []
                    for path in files_from_token:
                        textures_from_token.append(self.create_texture_item(path))

                    
                    if not exists :
                        texture_item = TextureFrames(name=name, texture_path='', nodes=[node_name], children=textures_from_token)
                    #texture_item = self.create_item(name , files_from_token , [])

                    attr_str = ""
            # 

            if (not attr_str in self.texture_paths) and attr_str: 
                self.texture_paths.append(attr_str)
                if not exists :
                    texture_item = TextureFile(name=name, texture_path=attr_str, nodes=[node_name])
                #texture_item = self.create_item(name , attr_str , [])

            if texture_item and (not texture_item in self.texture_items) : 
                self.texture_items.append(texture_item)

    def create_texture_item(self, filepath, nodes=[]):
        name = self.get_texture_name(filepath)
        return TextureFile(name=name , texture_path=filepath, nodes=nodes)

    #--------------------- Converter Methods ----------------------

    def find_convert_files(self):
        """
            Using texture paths, look for all their corresponding .rat files in the folder
            Basic parser 

            Output : List of files to convert
        """

        checked_dirs = []

        for item in self.texture_items :
                        
            files_to_convert = item.get_textures_paths()

            for texture_path in files_to_convert : 
                #here
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

                        rat = texture_path + ".rat"

                        dir_path = Path(dir_file)
                        dir_file_path = Path(tex_dir_path) / dir_path

                        if dir_file_path == Path(rat) :
                            
                            if texture_path in files_to_convert : 
                                files_to_convert.remove(texture_path)

            item.to_convert = len(files_to_convert)
            self.files_to_convert.extend(files_to_convert)

    def convert_to_rat(self, files_to_convert = None , threads = None,  path = None):
        """
            Converts a list of textures to .rat files, by calling workerthreads.  
            Saves them to the given path, if not specified saves them to the same path as the texture.
        """

        if files_to_convert :
            textures_list = files_to_convert 
        else : 
            textures_list = self.get_all_files_to_convert()

        if len(textures_list) <= 0 : 
            if self.ui : 
                self.ui.conversion_progress.setMaximum(1)
                self.ui.conversion_progress.setValue(1)
            return

        if not textures_list:
            return None

        if not threads : 
            threads = self.cpu_threads_default

        if not path : 
            path = os.path.abspath(os.path.join(textures_list[0], os.pardir)) 
        
        task_queue = queue.Queue()
        for tex in textures_list : 
            task_queue.put(tex)
        
        num_threads = min(threads, task_queue.qsize())

        self.workers = []
        self.finished_workers = 0
        self.total_workers = num_threads
        
        for i in range(num_threads):
            proc = WorkerThread(task_queue, output_path=path, id=i)
            # Connect signals to UI updates
            if self.ui:
                proc.inc_signal.connect(self.ui.update_progress)
                proc.finished_signal.connect(self.on_worker_finished)
            proc.start()
            self.workers.append(proc)

        # Don't block here - let signals handle completion
        print("Rat conversion : All workers started")

    def on_worker_finished(self, worker_id):
        """Called when a worker thread finishes"""
        self.finished_workers += 1
        print(f"Worker {worker_id} finished. {self.finished_workers}/{self.total_workers} complete.")
        
        if self.finished_workers >= self.total_workers:
            print("Rat conversion : All workers finished")
            # Refresh the UI after all conversions complete
            if self.ui:
                self.ui.on_conversion_complete()

    def add_accepted_nodes(self, nodes : list[str]) :
        for val in nodes : 
            if not val in self.accepted_nodes : 
                self.accepted_nodes.append(val)

    def remove_accepted_nodes(self, nodes : list[str]):
        for val in nodes:
            while val in self.accepted_nodes:
                self.accepted_nodes.remove(val)
    
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
        for item in self.texture_items : 
            textures.extend(item.texture_path)
        
        return list(set(textures))

    def get_all_files_to_convert(self):

        textures = []
        for item in self.texture_items : 
            textures.extend(item.get_convert_paths())

        return list(set(textures))
    
    def get_all_names(self):

        names = []
        for item in self.texture_items : 
            names.append(item.name)

        return names

#endregion
#endregion