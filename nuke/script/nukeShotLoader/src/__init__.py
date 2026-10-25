"""nukeShotLoader — loads Prism shot assets into Nuke and drives precomp/compo renders.

Package layout:
    core/     pure Python (no nuke, no Qt): config, disk discovery, versions,
              statuses, prefs, shared JSON files
    scene/    Nuke node-graph operations (no Qt)
    precomp/  precomp caching v2 (see its __init__)
    ui/       Qt dialog (qt.py: PySide2 / PySide6 binding)

Only v1 compatibility files live at this level, on purpose: scripts saved
with the v1 precomp setup exec the render hooks by absolute path
(before_render_precomp.py, after_render_precomp.py,
after_compo_render_diagnostic.py) and import `module_precomp` by name, this
folder being on sys.path. Nothing else belongs here: every module at this
level is importable by name by every tool of the pipeline.

Kept free of imports so importing a sub-package never drags Qt in.
"""

__version__ = "2.3.0"
