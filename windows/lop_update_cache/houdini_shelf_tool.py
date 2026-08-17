# -*- coding: utf-8 -*-
"""
Shelf tool Houdini pour lancer l'UI "CFX Re-cache".

A coller dans un bouton de shelf. Il lance l'UI en PROCESS SEPARE (option B :
l'UI tourne dans son propre env uv/PySide6, pas dans le Qt de Houdini) et lui
passe le PROJET Prism courant + la scene courante via des variables d'env, pour
que l'artiste n'ait RIEN a chercher/saisir.

L'UI lit :
  - LOP_UPDATE_CACHE_PROJECT = chemin du pipeline.json (projet auto-detecte)
  - LOP_UPDATE_CACHE_HIP     = scene .hip courante (pre-remplissage si rien de memorise)
Si le projet Prism n'est pas recuperable, la scene suffit : l'UI derive le
projet en remontant jusqu'a 00_Pipeline/pipeline.json.
"""

import os
import subprocess

ROOT = r"R:\pipeline\pipe\windows\lop_update_cache"

env = dict(os.environ)

# --- projet Prism courant (pipeline.json) ---
try:
    import PrismInit

    pcore = getattr(PrismInit, "pcore", None) or getattr(PrismInit, "core", None)
    proj = getattr(pcore, "prismIni", "") if pcore else ""
    if proj and os.path.isfile(proj):
        env["LOP_UPDATE_CACHE_PROJECT"] = proj
except Exception:
    pass

# --- scene courante (fallback pour deriver le projet, + pre-remplissage) ---
try:
    import hou

    hip = hou.hipFile.path()
    if hip and os.path.isfile(hip):
        env["LOP_UPDATE_CACHE_HIP"] = hip
except Exception:
    pass

subprocess.Popen([ROOT + r"\main_ui.bat"], cwd=ROOT, shell=True, env=env)
