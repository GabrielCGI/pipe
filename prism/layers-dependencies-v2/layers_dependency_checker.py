from pathlib import Path

from src.core import get_status_tree
from src.ui import open_tree_ui

import sys
import os

# Sequence names to ignore entirely (case-insensitive substring)
SEQUENCE_FILTER = ["SANDBOX", "TURN"]

# Shot identifiers to ignore (format: "SEQ_SHOT", e.g.: "CAPS-03_SH0300")
SHOT_FILTER = ["_sequence"]


def run():
    # prepare PrismCore path and import inside main to avoid background work at import time
    prism_scripts = r"C:\ILLOGIC_APP\Prism\2.0.18\app\Scripts"
    prism_scripts = os.path.normpath(prism_scripts)
    sys.path.insert(0, prism_scripts)

    try:
        import PrismCore
    except Exception as e:
        print("Failed to import PrismCore:", e)
        raise

    # create core and project browser
    core = PrismCore.create(prismArgs=["noUI", "loadProject"])
    core.projectBrowser(False)

    # compute ROOT now that core exists
    root_path = Path(core.projectPath) / "03_Production" / "Shots"

    tree = get_status_tree(root_path)

    # apply sequence filter and shot filter (case-insensitive)
    seq_filter_lower = [s.lower() for s in SEQUENCE_FILTER]
    shot_filter_lower = [s.lower() for s in SHOT_FILTER]

    filtered = {}
    for seq_name, shots in tree.items():
        if any(filt in seq_name.lower() for filt in seq_filter_lower):
            continue
        shot_node = {}
        for shot_name, layers in shots.items():
            shot_id = f"{seq_name}_{shot_name}".lower()
            # ignore si un des filtres est une sous-chaîne de shot_id
            if any(filt in shot_id for filt in shot_filter_lower):
                continue

            # si au moins un layer n'est pas considéré missing ou N/A -> garder le shot
            keep_shot = False
            for info in layers.values():
                status = info.get("status")
                if status != "missing" and status != "N/A":
                    keep_shot = True
                    break

            if keep_shot:
                shot_node[shot_name] = layers

        if shot_node:
            filtered[seq_name] = shot_node

    open_tree_ui(filtered, title="Layers Dependency Check - " + core.projectName, core=core)

if __name__ == "__main__":
    run()
