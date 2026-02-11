import nuke


def retrack_every_nodes():
    found_list = []
    for node in nuke.allNodes():
        if "nametag" in node.knobs() and node["nametag"].value() == "ILGC_OFTracker":
            found_list.append(node.name())
            node["launchTrack"].execute()
    if not len(found_list):
        nuke.message("Did not found any node to retrack")
        # print("Did not found any node to retrack")
    else:
        msg = f"Retracked {len(found_list)} nodes:\n"
        for node in found_list:
            msg += f" - {node}\n"
        nuke.message(msg)
        # print(msg)


def retrack_selected_nodes():
    found_list = []
    for node in nuke.selectedNodes():
        if "nametag" in node.knobs() and node["nametag"].value() == "ILGC_OFTracker":
            found_list.append(node.name())
            node["launchTrack"].execute()
    if not found_list:
        nuke.message("Did not found any node to retrack")
        # print("Did not found any node to retrack")
    else:
        msg = f"Retracked {len(found_list)} nodes:\n"
        for node in found_list:
            msg += f" - {node}\n"
        nuke.message(msg)
        # print(msg)