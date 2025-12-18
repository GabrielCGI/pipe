import re
import nuke


VERSION_PATTERN = r"v\d{3,9}"

def retrieve_read_files():
    """
    Retrieve all the files from read nodes.
    :return:
    """
    read_nodes = nuke.allNodes("Read")
    read_nodes += nuke.allNodes("DeepRead")
    read_files = []
    version_pattern_cmp = re.compile(VERSION_PATTERN)
    for node in read_nodes:
        file_path = node["file"].value()
        match = version_pattern_cmp.search(file_path)
        if match:
            version_span = match.span(0)
            read_files.append(file_path[:version_span[1]])

    return read_files