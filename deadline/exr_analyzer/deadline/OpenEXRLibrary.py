"""
OpenEXRLibrary.py  —  Script Deadline Monitor (menu General)
Ouvre la librairie EXR Analyzer dans le navigateur par défaut.

Installation :
    Copier ce fichier dans <DeadlineRepository>/custom/scripts/General/
"""

import os

REPORTS_DIR = r"R:\pipeline\pipe\deadline\exr_analyzer\reports"


def __main__(*args):
    index = os.path.join(REPORTS_DIR, "index.html")
    if os.path.isfile(index):
        os.startfile(index)
    else:
        from Deadline.Scripting import ClientUtils
        ClientUtils.LogText(f"EXR Library : index.html introuvable dans {REPORTS_DIR}")
