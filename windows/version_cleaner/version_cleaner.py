
import os
from pathlib import Path
import re
import glob
import logging
import time

import progressbar

PREFIX_TO_DELETE = "_TO_DELETE_"

# Init logger
# logging.basicConfig(format="%(asctime)s | %(message)s",\
#     datefmt="%Y/%m/%d %I:%M:%S%p")
LOG = logging.getLogger("Python | {file_name}".format(file_name=__name__))
LOG.setLevel(level=logging.INFO)


def get_directory_size(directory: Path) -> int:
    """
    Returns the total size of files in the directory 
    and its subdirectories in bytes.
    """
    total_size = 0
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            # Add file size if it's a file
            if file_path.is_file():
                total_size += file_path.stat().st_size
    return total_size


def parse_directories_sizes(directories: list[Path]):
    """
    Parses the sizes of a list of directories 
    and returns them as a dictionary.
    """
    sizes = {}
    for directory in directories:
        if directory.is_dir():
            sizes[directory] = get_directory_size(directory)
    return sizes

class Cleaner():
    def __init__(self, folder: str, version_to_save: int,\
        key_to_delete: set={"3dRender"}):
        
        self.folder = folder
        self.version_to_save =version_to_save
        
        self.key_to_not_delete = key_to_delete
        self.version_to_flag = {}
        
    def retrieveVersionToFlag(self):
        
        if self.folder is None:
            return
        
        pattern = os.path.join(self.folder, "**" + os.sep)
        version_pattern = r"^v\d+"
        
        time_taken = time.time()
        
        object_versions = {}
        file_to_inspect = glob.glob(pathname=pattern, recursive=True)
        
        # Get every versions in the folder
        for filepath in file_to_inspect:
            
            to_be_deleted = True
            for key in self.key_to_not_delete:
                if key in filepath:
                    to_be_deleted = False
                    
            if not to_be_deleted:
                continue
                
            filepath = os.path.dirname(filepath)
            basename = os.path.basename(filepath)
            match = re.search(version_pattern, basename)
            
            if match is not None:
                dirname = os.path.dirname(filepath)
                if dirname in object_versions:
                    object_versions[dirname].append(filepath)
                else:
                    object_versions[dirname] = [filepath]
        
        total_version = 0
        versions_to_flags = {}
        
        # Get every version to delete
        for dirname, versions in object_versions.items():
            versions.sort(reverse=True)
            total_version += len(versions)
            if len(versions) > self.version_to_save:
                versions_to_flags[dirname] = []
            for i in range(len(versions)):
                if i+1 > self.version_to_save:
                    versions_to_flags[dirname].append(versions[i])
        
        # Get every size in bytes of versions to delete
        LOG.info("Compute file sizes ... ")
        with progressbar.ProgressBar(max_value=len(versions_to_flags)) as bar:
            i = 0
            for dirname, versions in versions_to_flags.items():
                versions_paths = []
                for v in versions:
                    versions_paths.append(Path(v))
                sizes = parse_directories_sizes(versions_paths)
                for directory, size in sizes.items():
                    self.version_to_flag[dirname] = (directory, size)
                bar.update(i)
                i += 1

        total_size = 0
        for _, path_info in self.version_to_flag.items():
            total_size += path_info[1]
            
        time_taken = time.time() - time_taken
        LOG.info(f"Number of versions to save: {self.version_to_save}")
        LOG.info(f"Total files found: {len(file_to_inspect)}")
        LOG.info(f"Total objects found: {len(object_versions)}")
        LOG.info(f"Total version found: {total_version}")
        LOG.info(f"Total version to clean: {len(self.version_to_flag)}")
        LOG.info(f"Total size to clean: {total_size / (1024 ** 2):.2f} MB")
        LOG.info(f"Time taken: {str(time_taken)[:4]} s")
    
    def renameVersions(self):
        LOG.info("Rename files ... ")
        with progressbar.ProgressBar(max_value=len(self.version_to_flag))\
            as bar:
            i = 0
            for _, path_info in self.version_to_flag.items():
                dirname = os.path.dirname(path_info[0])
                basename = os.path.basename(path_info[0])
                newpath = os.path.join(dirname, PREFIX_TO_DELETE + basename)
                os.rename(path_info[0], newpath)
                bar.update(i)
                i += 1
        LOG.info("Renaming done.")
    
    
if __name__ == "__main__":
    path = r"I:\tmp\resolver_RND2_test_cleaner"
    cleaner = Cleaner(path, 1)
    
    cleaner.retrieveVersionToFlag()
    cleaner.renameVersions()