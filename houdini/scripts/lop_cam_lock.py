# Illogic Studios "LM Fix" - Light Mixer look-through fix.
#
# DEPLOYMENT --------------------------------------------------------------
# This file lives in R:/pipeline/pipe/houdini/scripts, which is NOT on any
# Houdini search path: it is loaded as a plain module, by absolute path, by
# the "LM Fix ON/OFF" tool of illogic_Lighting.shelf, which calls toggle().
# The fix is applied by a session monkeypatch on loputils.createEditorNode
# (see the bottom of this file), so nothing depends on HOUDINI_PATH.
#
# The file also remains a valid drop-in override of $HFS/houdini/scripts/
# scene/lop_cam_lock.py: copied into <any HOUDINI_PATH entry before $HFS>/
# scripts/scene/, handleViewChange() below replaces the stock callback.
#
# WHY --------------------------------------------------------------------
# Stock Houdini can never write a look-through ("lock camera/light to view")
# move into a Light Mixer: getExistingEditorNode() only reuses a node whose
# lastModifiedPrims() is exactly [the prim], which a mixer authoring several
# lights never satisfies, so Houdini spawns an edit_<light> Light LOP.
#
# WHAT -------------------------------------------------------------------
# Behavior is stock except one branch: when no dedicated editor node exists
# for a light and a non-bypassed Light Mixer upstream of the viewed node owns
# it (in its layout or its Transforms delta), the move is written into that
# mixer's delta geometry, using the same encoding the mixer's handle-drag
# absorb produces:
#
#     delta_xform = desired_local_xform * input_local_xform^-1
#     (P stays 0; keepposition/twist stay 1)
#
# Encoding validated empirically on Houdini 21.0.729. Every write is verified
# against the mixer's output stage and undone on mismatch; any error falls
# back to the stock code path (edit_<light> creation). Autokey always uses
# the stock path, because the mixer delta is not keyable.
#
# ACTIVATION -------------------------------------------------------------
# Per user/session via the ILLOGIC_LMFIX variable ('1' = on, anything else =
# stock behavior). The LM Fix shelf toggle flips it live (hou.putenv); set
# ILLOGIC_LMFIX=1 in the launch environment (houdini.env / package / Prism)
# for a default-on studio deploy. This file is never modified at runtime, so
# it can be shared read-only by any number of users.
#
# UNINSTALL: delete this file.

import json
import time
import traceback

import hou
import loputils
import nodegraphutils
from pxr import Sdf
from pxr import Usd
from pxr import UsdGeom
from pxr import UsdLux

# ======================================================================
# Stock implementation, verbatim from
# $HFS/houdini/scripts/scene/lop_cam_lock.py (Houdini 21.0.729)
# ======================================================================

def isValidEditorNode(node, viewnode, primpath):
    # The specified prim must exist on the node's stage.
    prim = node.stage().GetPrimAtPath(primpath)
    if not prim:
        return False

    # If any of our ancestor prims are edited by a node that is connected to
    # the output of this node, we can't use this node. Otherwise a transform
    # LOP may move /cameras/rig, affecting /cameras/rig/left.
    alloutputs = set()
    cookpathnodes = set(viewnode.cookPathNodes())
    nodegraphutils.getOutputsRecursive(node, alloutputs)
    parentpath = Sdf.Path(primpath).GetParentPath()
    while parentpath != Sdf.Path.absoluteRootPath:
        primeditornodes = loputils.getEditorNodes(
            viewnode, parentpath, allow_locked_nodes = True)
        for editornode in primeditornodes:
            if editornode in alloutputs and editornode in cookpathnodes:
                return False
        parentpath = parentpath.GetParentPath()

    # If the editor node modified more than just this one prim, we don't want
    # to reuse it, because we don't want to change other prims.
    if list(node.lastModifiedPrims()) != [ primpath ]:
        return False

    # The node must have the parms we use to set the transform.
    if node.parmTuple('t') is None or \
       node.parmTuple('r') is None:
        return False

    return True

def getExistingEditorNode(node, primpath):
    editornodes = loputils.getEditorNodes(
        node, primpath, allow_locked_nodes = True)
    if editornodes and isValidEditorNode(editornodes[-1], node, primpath):
        return editornodes[-1]
    return None

def _applyViewChange(viewparms, viewxform, node, primpath,
                     editornode, iscam, islight, msg):
    changed_anything = False
    try:
        with hou.undos.group(msg):
            # If we don't find one, create it. This is our last attempt.
            if editornode is None:
                editornode = loputils.createEditorNode(
                    node, primpath, None, [primpath],
                    respect_insertion_point=False)

            # Get the transform of this prim according to our input node.
            # Because we always append a new xform with the editor node,
            # the inverse of the xform before this node needs to be applied
            # to the view xform to figure out the xform this node needs to
            # append to end up with the xform we want.
            #
            # If we don't have an input node, or this prim doesn't exist on
            # the input node, then this editor node must be creating the prim,
            # so we don't need to compensate for any existing transformations.
            parentxform = hou.Matrix4(1.0)
            inputnode = editornode.input(0)
            if inputnode is not None:
                inputprim = inputnode.stage().GetPrimAtPath(primpath)
                inputimageable = UsdGeom.Imageable(inputprim)
                if inputimageable:
                    timecode = Usd.TimeCode(hou.frame())
                    inputxform = hou.Matrix4(
                        inputimageable.ComputeLocalToWorldTransform(timecode))
                    parentxform = inputxform.inverted()

            # If the camera prim is parented to a transformed prim,
            prim = node.stage().GetPrimAtPath(primpath)
            if prim:
                parent = prim.GetParent()
                if prim:
                    inputimageable = UsdGeom.Imageable(parent)
                    if inputimageable:
                        timecode = Usd.TimeCode(hou.frame())
                        inputxform = hou.Matrix4(
                            inputimageable.ComputeLocalToWorldTransform(timecode))
                        parentxform = parentxform * inputxform.inverted()

            # Set the xform control parm to "Set or Create". If the parm doesn't
            # exist, assume this is an HDA configured so that this control parm
            # isn't needed or is always set properly.
            cp = editornode.parm(hou.text.encodeParm("xformOp:transform_control"))
            if cp is not None and cp.eval() != 'set':
                cp.set("set")
                # If we reach this point, we've made a change that may
                # need to be undone if we fail past this point.
                changed_anything = True

            # From the view transform and the target prim's transform before
            # applying the transform from this node, figure out the local
            # transform we need on the prim.
            localxform = viewxform * parentxform

            # Set the translate and rotate for the camera's or light's local
            # transform. This may throw an exception if the parms are not
            # editable (and not promoted).
            if hou.ui.isAutoKey():
                editornode.parmTuple('t').set(localxform.extractTranslates())
            else:
                editornode.parmTuple('t').setPending(localxform.extractTranslates())
            # If we reach this point, we've made a change that may
            # need to be undone if we fail past this point.
            changed_anything = True
            if hou.ui.isAutoKey():
                editornode.parmTuple('r').set(localxform.extractRotates())
            else:
                editornode.parmTuple('r').setPending(localxform.extractRotates())

            if iscam:
                if viewparms.isPerspective():
                    projection = 'perspective'
                else:
                    projection = 'orthographic'
                projparm = editornode.parm('projection')
                if projparm is not None and projparm.eval() != projection:
                    if hou.ui.isAutoKey():
                        projparm.set(projection)
                    else:
                        projparm.setPending(projection)


            # Success! Set all required parameters without any errors.
            return True

    except hou.PermissionError:
        if changed_anything:
            hou.undos.performUndo()

    return False

# ======================================================================
# Illogic addition: absorb look-through light moves into the Light Mixer
# ======================================================================

_XFORM_TOL = 1e-3
_IDENTITY16 = (1.0, 0.0, 0.0, 0.0,
               0.0, 1.0, 0.0, 0.0,
               0.0, 0.0, 1.0, 0.0,
               0.0, 0.0, 0.0, 1.0)

# Point attribute schema of the lightmixer 'delta' geometry as shipped in
# Houdini 21.0 (captured from a live mixer). Only used to create missing
# attributes when inserting into a delta that does not have them yet.
_DELTA_SCHEMA = (
    ('primpath', ''),
    ('lookatprim', ''),
    ('xform', _IDENTITY16),
    ('distance', 1.0),
    ('spotlightdist', 1.0),
    ('keepposition', 1.0),
    ('twist', 1.0),
    ('lookatposition', (0.0, 0.0, 0.0)),
    ('lookatprimpos', (0.0, 0.0, 0.0)),
    ('lookatprimrot', (0.0, 0.0, 0.0)),
    ('shadowpivot', (0.0, 0.0, 0.0)),
    ('shadowtarget', (0.0, 0.0, 0.0)),
    ('hitpos', (0.0, 0.0, 0.0)),
    ('hitnormal', (0.0, 0.0, 0.0)),
    ('lookatenable', 0),
    ('hit', 0),
    ('hasshadowpivot', 0),
    ('hasshadowtarget', 0),
)

_target_mixer_cache = {}

def _mixerContainsLight(mixer, primpath):
    # The light is owned by this mixer when it is present in its Transforms
    # delta or anywhere in its UI layout (including inside collections).
    try:
        geo = mixer.parm('delta').evalAsGeometry()
        if geo is not None and geo.findPointAttrib('primpath') is not None:
            for pt in geo.points():
                if pt.stringAttribValue('primpath') == primpath:
                    return True
        layout = mixer.evalParm('setting_layout')
        if layout:
            def _walk(items):
                for item in items:
                    if item.get('prim_path') == primpath:
                        return True
                    if _walk(item.get('contents') or []):
                        return True
                return False
            return _walk(json.loads(layout))
    except Exception:
        pass
    return False

def _findTargetMixer(viewnode, primpath):
    # Most-downstream non-bypassed Light Mixer upstream of (or at) the viewed
    # node that owns this light. None when there is no unambiguous owner.
    key = (viewnode.sessionId(), primpath)
    cached = _target_mixer_cache.get(key)
    if cached is not None:
        try:
            if not cached.isBypassed() and _mixerContainsLight(cached, primpath):
                return cached
        except hou.ObjectWasDeleted:
            pass
        _target_mixer_cache.pop(key, None)

    candidates = []
    for n in list(viewnode.inputAncestors()) + [viewnode]:
        if n.type().name() != 'lightmixer' or n.isBypassed():
            continue
        if _mixerContainsLight(n, primpath):
            candidates.append(n)

    if len(candidates) > 1:
        candidates = [c for c in candidates
                      if not any(c in o.inputAncestors()
                                 for o in candidates if o is not c)]

    if len(candidates) != 1:
        return None
    _target_mixer_cache[key] = candidates[0]
    return candidates[0]

def _writeMixerDelta(mixer, primpath, delta_xform):
    parm = mixer.parm('delta')
    src = parm.evalAsGeometry()
    geo = hou.Geometry()
    if src is not None:
        geo.merge(src)

    for name, default in _DELTA_SCHEMA:
        if geo.findPointAttrib(name) is None:
            geo.addAttrib(hou.attribType.Point, name, default)

    target = None
    for pt in geo.points():
        if pt.stringAttribValue('primpath') == primpath:
            target = pt
            break
    if target is None:
        target = geo.createPoint()
        target.setAttribValue('primpath', primpath)

    target.setAttribValue('xform', delta_xform.asTuple())
    parm.set(geo)

def _applyViewChangeToMixer(viewxform, mixer, primpath, msg):
    # Write the desired world transform into the mixer's Transforms delta.
    # Returns True only when the mixer's output stage verifiably shows the
    # requested transform afterwards; otherwise the write is undone. This
    # guards against the (undocumented) delta encoding changing in a future
    # Houdini build: on mismatch the stock path takes over.
    inputnode = mixer.input(0)
    if inputnode is None:
        return False
    instage = inputnode.stage()
    if instage is None:
        return False
    inprim = instage.GetPrimAtPath(primpath)
    if not inprim or not inprim.IsValid():
        return False
    inxformable = UsdGeom.Xformable(inprim)
    if not inxformable:
        return False

    timecode = Usd.TimeCode(hou.frame())
    in_local = hou.Matrix4(inxformable.GetLocalTransformation(timecode))

    parent_world = hou.Matrix4(1.0)
    parent = inprim.GetParent()
    if parent and parent.IsValid():
        parentimageable = UsdGeom.Imageable(parent)
        if parentimageable:
            parent_world = hou.Matrix4(
                parentimageable.ComputeLocalToWorldTransform(timecode))

    try:
        desired_local = viewxform * parent_world.inverted()
        delta_xform = desired_local * in_local.inverted()
    except hou.OperationFailed:
        return False

    with hou.undos.group(msg):
        _writeMixerDelta(mixer, primpath, delta_xform)

    verified = False
    outstage = mixer.stage()
    if outstage is not None:
        outprim = outstage.GetPrimAtPath(primpath)
        if outprim and outprim.IsValid():
            outxformable = UsdGeom.Xformable(outprim)
            if outxformable:
                out_local = hou.Matrix4(
                    outxformable.GetLocalTransformation(timecode))
                verified = out_local.isAlmostEqual(desired_local, _XFORM_TOL)

    if not verified:
        hou.undos.performUndo()
    return verified

# ======================================================================
# Entry point (stock, plus the Light Mixer branch)
# ======================================================================

def handleViewChange(viewer, viewport, viewparms, viewxform, node, primpath):
    # Beacon for the LM Fix shelf tools: proves this override file (not the
    # $HFS stock copy) is the one the viewport is executing.
    hou.putenv('ILLOGIC_LMFIX_BEACON',
               'fichier override @ ' + time.strftime('%H:%M:%S'))
    prim = node.stage().GetPrimAtPath(primpath)
    if not prim.IsValid():
        return
    iscam = prim.IsA(UsdGeom.Camera)
    islight = prim.HasAPI(UsdLux.LightAPI)
    if not iscam and not islight:
        return

    editableattr = prim.GetAttribute('houdini:editable')
    if editableattr and editableattr.Get() == False:
        viewer.flashMessage('STATUS_error',
            'Camera is not editable' if iscam else 'Light is not editable')
        return

    if iscam:
        msg = "Set Camera to View"
    else:
        msg = "Set Light to View"

    # Find an existing node for editing the camera or light prim.
    editornode = getExistingEditorNode(node, primpath)

    # Illogic override: when stock would create a new edit_<light> node,
    # absorb the move into the Light Mixer that owns this light instead.
    # Opt-in per user/session: only when ILLOGIC_LMFIX=1 (set by the LM Fix
    # shelf toggle, or in the launch environment for a studio-wide default).
    if (editornode is None and islight and not hou.ui.isAutoKey()
            and hou.getenv('ILLOGIC_LMFIX') == '1'):
        try:
            mixer = _findTargetMixer(node, primpath)
            if mixer is not None and \
                    _applyViewChangeToMixer(viewxform, mixer, primpath, msg):
                return
        except Exception:
            # Never break the viewport: report and fall back to stock.
            traceback.print_exc()

    if not _applyViewChange(viewparms, viewxform, node, primpath,
                            editornode, iscam, islight, msg):
        if editornode is not None:
            _applyViewChange(viewparms, viewxform, node, primpath,
                             None, iscam, islight, msg)

# ======================================================================
# Session toggle (used by the "LM Fix ON/OFF" shelf tool)
# ======================================================================
#
# Works even though this file is not on the Houdini script search path:
# the first ON installs a session monkeypatch on loputils.createEditorNode.
# The stock lock-to-view callback necessarily calls it to create its
# edit_<light> node; the patch intercepts that call (argument fingerprint)
# and returns a shim that captures the t/r values the stock code pushes,
# routing them into the Light Mixer instead. Both the patch and
# handleViewChange() above are gated by ILLOGIC_LMFIX ('1' = on), so OFF
# neutralizes everything without uninstalling.

class _ShimParmTuple(object):
    def __init__(self, node, key):
        self._node = node
        self._key = key
    def set(self, values):
        self._node._store(self._key, values)
    def setPending(self, values):
        self._node._store(self._key, values)


class _ShimNode(object):
    # Duck-types just what the stock _applyViewChange uses on the editor
    # node: input(0), parm(...), parmTuple('t'/'r').
    def __init__(self, mixer, primpath):
        self._mixer = mixer
        self._primpath = primpath
        self._vals = {}
    def input(self, idx):
        return self._mixer.input(0)
    def parm(self, name):
        return None
    def parmTuple(self, name):
        if name in ('t', 'r'):
            return _ShimParmTuple(self, name)
        return None
    def _store(self, key, values):
        self._vals[key] = tuple(values)
        if 't' in self._vals and 'r' in self._vals:
            vals = self._vals
            self._vals = {}
            self._fire(vals)
    def _fire(self, vals):
        try:
            hou.putenv('ILLOGIC_LMFIX_BEACON',
                       'patch session (shim) @ ' + time.strftime('%H:%M:%S'))
            local = hou.hmath.buildTransform(
                {'translate': vals['t'], 'rotate': vals['r']})
            inputnode = self._mixer.input(0)
            prim = inputnode.stage().GetPrimAtPath(self._primpath)
            in_local = hou.Matrix4(UsdGeom.Xformable(prim)
                .GetLocalTransformation(Usd.TimeCode(hou.frame())))
            world = local * in_local
            _applyViewChangeToMixer(world, self._mixer, self._primpath,
                                    'Set Light to View')
        except Exception:
            traceback.print_exc()


def _installSessionShim():
    if getattr(hou.session, 'illogic_lmfix', None) is not None:
        return
    orig = loputils.createEditorNode

    def _patched(sourcenode, primpath, classancestor, primpaths,
                 respect_insertion_point=True, prefix='edit_', suffix='',
                 make_editor_node_current=False):
        # Only intercepts when the flag is on, for the lock-to-view
        # callback's call (argument fingerprint), on a light owned by a
        # mixer, outside autokey.
        try:
            if hou.getenv('ILLOGIC_LMFIX') == '1':
                camlock = (respect_insertion_point is False
                           and classancestor is None
                           and list(primpaths) == [primpath]
                           and prefix == 'edit_')
                if camlock and not hou.ui.isAutoKey():
                    mixer = _findTargetMixer(sourcenode, primpath)
                    if mixer is not None:
                        return _ShimNode(mixer, primpath)
        except Exception:
            traceback.print_exc()
        return orig(sourcenode, primpath, classancestor, primpaths,
                    respect_insertion_point=respect_insertion_point,
                    prefix=prefix, suffix=suffix,
                    make_editor_node_current=make_editor_node_current)

    loputils.createEditorNode = _patched
    hou.session.illogic_lmfix = {'orig': orig}


def toggle():
    # Entry point of the "LM Fix ON/OFF" shelf tool.
    if hou.getenv('ILLOGIC_LMFIX') == '1':
        hou.putenv('ILLOGIC_LMFIX', '0')
        hou.ui.setStatusMessage(
            'LM Fix OFF - comportement stock (creation de edit_<light>)',
            hou.severityType.ImportantMessage)
    else:
        _installSessionShim()
        hou.putenv('ILLOGIC_LMFIX', '1')
        hou.ui.setStatusMessage(
            'LM Fix ON - les moves look-through vont dans le Light Mixer',
            hou.severityType.ImportantMessage)
