# v1 render hook, kept only so scripts not yet upgraded to precomp v2 still
# render (exec'd by path from the v1 PrecompWrite / WriteCompo beforeRender).
# v1 switches route live (src/module_precomp.py), so no v1 PrecompWrite needs
# to read its render back: `reading` is turned off on the farm, where a
# PrecompWrite reading its own missing output logs "ERROR: ... Read error"
# and Deadline fails the task on any "ERROR:" line.
import nuke as _nuke

if not _nuke.GUI:
    for _write in _nuke.allNodes("Write", recurseGroups=True):
        _tag, _reading = _write.knob("tag"), _write.knob("reading")
        if _tag is not None and _tag.value() == "PrecompWrite" and _reading is not None and _reading.value():
            _reading.setValue(False)
print("[precomp] v1 script rendered without precomp caching — upgrade it (Render Manager > Upgrade Precomps)")
