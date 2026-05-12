"""
Standalone copy worker — no Qt dependency.
Called by CopyToCloud.py as a background subprocess.

Usage: python _copy_worker.py <src> <dst> <decisions_json>

decisions_json: path to a JSON file mapping normalized dst folder paths -> bool (True = overwrite existing files)
The worker deletes the decisions file when done.
On error, shows a native Windows message box.
"""

import os
import sys
import json
import shutil
import ctypes


def msg_error(text):
    ctypes.windll.user32.MessageBoxW(0, text, "CopyToCloud — Error", 0x10)


def copy_file(src, dst, overwrite):
    if os.path.exists(dst):
        if overwrite:
            shutil.copy2(src, dst)
    else:
        shutil.copy2(src, dst)


def copy_dir(src_dir, dst_dir, decisions):
    os.makedirs(dst_dir, exist_ok=True)
    for item in os.listdir(src_dir):
        src_item = os.path.join(src_dir, item)
        dst_item = os.path.join(dst_dir, item)
        if os.path.isdir(src_item):
            copy_dir(src_item, dst_item, decisions)
        elif os.path.isfile(src_item):
            overwrite = decisions.get(os.path.normpath(dst_dir), True)
            copy_file(src_item, dst_item, overwrite)


if __name__ == "__main__":
    src, dst, decisions_path = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        with open(decisions_path, "r") as f:
            decisions = json.load(f)
    except Exception as e:
        msg_error(f"Failed to read decisions file:\n{e}")
        sys.exit(1)
    finally:
        try:
            os.remove(decisions_path)
        except Exception:
            pass

    try:
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            overwrite = decisions.get(os.path.normpath(dst), True)
            copy_file(src, dst, overwrite)
            explorer_target = os.path.dirname(dst)
        elif os.path.isdir(src):
            copy_dir(src, dst, decisions)
            explorer_target = dst
        else:
            msg_error(f"Source is not a file or folder:\n{src}")
            sys.exit(1)
    except Exception as e:
        msg_error(f"Copy failed:\n{e}")
        sys.exit(1)

    os.startfile(explorer_target)
