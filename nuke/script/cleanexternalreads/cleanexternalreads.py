import os
import shutil
import threading
import subprocess
import datetime
from pathlib import Path

import nuke

# flags to parse prism path
PRODUCTION_FLAG = "03_Production"
RENDER_FLAG = "Renders"

MAX_MSG_LIMIT = 5

LOG_DIR = "R:/logs/nuke_cleaner_logs"

IGNORE_LIST = [
    "I:/intermarche/03_Production/Shots/SQ080/SH0400/Renders/2dRender/PAINT_CHARS_IN/v001/SQ080-SH0400_PAINT_CHARS_IN_v001.1001.psd"
]

def get_connected_nodes(node: nuke.Node, collected=None) -> set:
    """
    Recursively get all nodes connected to the given node.
    """
    if collected is None:
        collected = set()

    if node is None or node in collected:
        return collected

    collected.add(node)

    for i in range(node.inputs()):
        input_node = node.input(i)
        if input_node is not None:
            get_connected_nodes(input_node, collected)

    return collected


def get_writing_nodes() -> set:
    """
    Get a set containing every node connect to a write node.
    """
    
    write_nodes = nuke.allNodes("Write")
    
    writing_nodes = set()
    for write in write_nodes:
        writing_nodes = get_connected_nodes(write, writing_nodes)
    
    return writing_nodes


def get_connected_reads(nodes: set) -> list:
    """
    Get every reads that are connected to given set.
    """
    
    read_nodes = set(nuke.allNodes("Read"))
    connected_reads = nodes.intersection(read_nodes)
    return list(connected_reads)
    

def get_writing_reads() -> list:
    """
    Get every reads that are conected to at least one write node.
    """
    writing_node = get_writing_nodes()
    return get_connected_reads(writing_node)


def createCopy(read_path: Path, destination_path: Path):
    """Create a copy using shutil.copytree of read_path directory
    and ignore it if destination path already exists.

    Args:
        read_path (Path): Orignal path in read nodes.
        destination_path (Path): New path local to shots.
    """
    
    if destination_path.exists():
        return
    shutil.copytree(src=read_path, dst=destination_path)
    

def getShotSequences(filepath: Path):
    """Get shot and sequence from filepath.

    Args:
        filepath (Path): File path from prism.

    Returns:
        tuple|None: Return None if failed to parse, else 
                    return a tuple with shot and sequence
    """
    
    split_path = filepath.parts
    if not PRODUCTION_FLAG in split_path:
        return
    prod_flag_idx = split_path.index(PRODUCTION_FLAG)
    if len(split_path) < prod_flag_idx + 3:
        return
    sequence = split_path[prod_flag_idx+2]
    shot = split_path[prod_flag_idx+3]
    return (sequence, shot)


def openReport(report: str):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_name = f"logs_nuke_cleaner_{timestamp}.log"
        os.makedirs(LOG_DIR, exist_ok=True)
        log_file = os.path.join(LOG_DIR, log_name)
        with open(log_file, "w+") as f:
            f.writelines(report)
        command = ["notepad.exe", log_file]
        subprocess.run(command)
    except Exception as e:
        print(e)
        return


def main(debug_mode=False, silent_mode=False):
    """Clean current nuke by copying to shot external shots references.

    Args:
        debug_mode (bool, optional): Enable extra pop up msg. Defaults to False.
        silent_mode (bool, optional): Fully silent mode without pop up at all.
                                      Defaults to False.
    """
    
    nuke_root: dict = nuke.root()
    try:
        nuke_root_name: nuke.File_Knob = nuke_root["name"]
    except:
        if debug_mode:
            nuke.alert("Cannot parse current scenefile path")
        return
    scene_path = Path(nuke_root_name.value())
    shot_data = getShotSequences(scene_path)
    if shot_data is None:
        if debug_mode:
            nuke.alert("Cannot find Sequence/Shots pattern in scenefile path")
        return
    scene_sequence, scene_shot = shot_data
    scene_shot_idx = scene_path.parts.index(scene_shot)
    scene_prefix = Path(*scene_path.parts[:scene_shot_idx+1])
    scene_identifier = f"{scene_sequence}_{scene_shot}"

    read_nodes = get_writing_reads()
    pair_to_copy = []
    msg = []
    for read in read_nodes:
        read_filepath_knob: nuke.File_Knob = read.knob("file")
        read_filepath = Path(read_filepath_knob.getText())
        
        ignore = False
        for ignore_pattern in IGNORE_LIST:
            if ignore_pattern == read_filepath.as_posix():
                ignore = True
                break
        if ignore:
            continue
                
        
        read_data = getShotSequences(read_filepath)
        if not read_data:
            continue
        read_sequence, read_shot = read_data
        read_identifier = f"{read_sequence}_{read_shot}"
        if read_identifier == scene_identifier:
            continue
        
        try:
            render_idx = read_filepath.parts.index(RENDER_FLAG)
        except ValueError as e:
            continue
            
        render_suffix_l = list(read_filepath.parts[render_idx:])
        render_suffix_l[2] = f"{render_suffix_l[2]}_{read_identifier}"
        render_suffix = Path(*render_suffix_l)
        destination_path = scene_prefix / render_suffix

        pair_to_copy.append(
            (read_filepath_knob, read_filepath.parent, destination_path)
        )
        msg.append(
            f"\t- {read.name()}\n"
            f"\t--> Read from {read_identifier}\n"
        )
    
    if not len(pair_to_copy):
        if debug_mode:
            nuke.alert("You don't have any reads from other shots")
        return
    
    if not silent_mode:
        accepted = nuke.ask(
            f"You have {len(pair_to_copy)} read from another shots\n"
            " Do you want to copy them to this one ?\n"
            f"{''.join(msg[:MAX_MSG_LIMIT])}..."
        )
        
        if not accepted:
            thread = threading.Thread(target=openReport, args=(msg,))
            thread.start()
            return
    
    for node, src, dst in pair_to_copy:
        createCopy(src, dst.parent)
        node.setText(dst.as_posix())

    if not silent_mode:
        nuke.alert("Copy completed !")
    
    
if __name__ == "__main__":
    main()
    