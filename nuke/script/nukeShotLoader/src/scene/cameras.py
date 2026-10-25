"""Camera nodes holding a camera exported to a file (USD).

A Camera3 renders from its knobs — animation curves saved with the script:
what the viewer and the farm use. With `read from file`, Nuke copies the
file's camera into those knobs, but only for a node whose properties panel
exists: on a camera never opened in the session, `reload` bumps its
counter and leaves the knobs alone. A new camera stays at the origin, an
updated one stays frozen on its previous version while its `file` knob
names the new one (measured in Nuke 15.1v5; knob flags and forceValidate
don't help, and terminal mode never loads).

So the Shot Loader does not rely on that import:

    bake_file()   reads the USD itself (pxr, shipped with Nuke) and writes
                  the same curves Nuke's import would, `read from file` off,
                  the `file` knob still naming the source. Checked against
                  Nuke's own evaluation of the knobs before it returns.
    load_file()   Nuke's import, with the panel opened for it: only for
                  files bake_file() declines (NotBakeable).

Cameras loaded before that (Shot Loader <= 2.1, or by hand) can still hold
an older version's camera, or the one of the scene preset they were created
from. Nothing shows it until the panel gets opened, which loads the file:
the camera changes and every cache downstream goes Live.

    out_of_sync() a camera with `read from file` whose knobs hold another
                  camera than its file: where they part, and which version
                  of the file they hold (sanity check, Loader status)
"""

import math
import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import nuke

from ..core.versions import version_int
from .utils import silent_popups

_USD_EXTENSIONS = (".usd", ".usda", ".usdc", ".usdz")
_SELECTED_PRIM_RE = re.compile(r"\+ (/\S+)")    # `scene_graph` knob: '{0} version: 1 + /cameras/rig/shotCam'
_MAX_FRAMES = 100000

# knob -> GfCamera value (one key per frame, like Nuke's import)
_LENS = (
    ("focal", lambda c: c.focalLength),
    ("haperture", lambda c: c.horizontalAperture),
    ("vaperture", lambda c: c.verticalAperture),
    ("near", lambda c: c.clippingRange.min),
    ("far", lambda c: c.clippingRange.max),
    ("focal_point", lambda c: c.focusDistance),
    ("fstop", lambda c: c.fStop),
)
_TRANSFORM = ("translate", "rotate", "scaling", "skew", "pivot", "uniform_scale")
_SETTINGS = ("read_from_file", "rot_order", "xform_order", "useMatrix")


class NotBakeable(Exception):
    """The file is outside what bake_file() reproduces exactly."""


# ---------------------------------------------------------------------------
# Baking a USD camera into the knobs
# ---------------------------------------------------------------------------

def bake_file(camera, path: str):
    """Write the camera of the USD file `path` into the node's knobs.

    Same result as Nuke's import (rot_order XYZ, xform_order SRT, one key
    per frame of the stage range) without depending on it: `read_from_file`
    ends up off and `file` names the source. Raises NotBakeable — the node
    untouched — for what this doesn't reproduce: other formats, Z-up
    stages, sheared or mirrored transforms, lens shift, orthographic
    cameras, several cameras with none selected."""
    path = path.replace("\\", "/")
    frames, matrices, lenses = _read_usd(path, _selected_prims(camera))
    rotations, scales = _decompose(matrices)

    saved = _snapshot(camera)
    try:
        _write_knobs(camera, path, frames, matrices, rotations, scales, lenses)
        _verify(camera, frames, matrices)
    except Exception as e:
        _restore(camera, saved)
        if isinstance(e, NotBakeable):
            raise
        raise NotBakeable(f"knobs not written ({type(e).__name__}: {e})")
    span = f"frames {frames[0]}-{frames[-1]}" if frames else "static"
    print(f"[cameras] {camera.name()}: camera baked from {path} ({span})")


def _read_usd(path: str, selected: List[str]) -> Tuple[Optional[List[int]], list, list]:
    """(frames or None for a static camera, world matrix per frame, GfCamera per frame)."""
    if not path.lower().endswith(_USD_EXTENSIONS):
        raise NotBakeable(f"not a USD file: {os.path.basename(path)}")
    try:
        from pxr import Gf, Usd, UsdGeom
    except ImportError as e:
        raise NotBakeable(f"USD Python modules unavailable ({e})")
    try:
        stage = Usd.Stage.Open(path)
    except Exception as e:
        stage = None
        print(f"[cameras] {path}: {e}")
    if not stage:
        raise NotBakeable(f"file not readable: {path}")
    if UsdGeom.GetStageUpAxis(stage) != UsdGeom.Tokens.y:
        raise NotBakeable("stage is not Y-up")
    prim = _camera_prim(stage, selected, UsdGeom)

    if stage.HasAuthoredTimeCodeRange():
        first, last = int(round(stage.GetStartTimeCode())), int(round(stage.GetEndTimeCode()))
    else:
        times = _sample_times(prim)
        first, last = (int(math.floor(times[0])), int(math.ceil(times[-1]))) if times else (None, None)
    if first is None:
        frames, times = None, [Usd.TimeCode.Default()]
    else:
        if not 0 <= last - first <= _MAX_FRAMES:
            raise NotBakeable(f"unusable frame range {first}-{last}")
        frames = list(range(first, last + 1))
        times = frames

    xformable, schema = UsdGeom.Xformable(prim), UsdGeom.Camera(prim)
    matrices, lenses = [], []
    for time in times:
        matrices.append(xformable.ComputeLocalToWorldTransform(time))
        lens = schema.GetCamera(time)
        if lens.projection != Gf.Camera.Perspective:
            raise NotBakeable("not a perspective camera")
        if abs(lens.horizontalApertureOffset) > 1e-9 or abs(lens.verticalApertureOffset) > 1e-9:
            raise NotBakeable("lens shift (aperture offset)")
        lenses.append(lens)
    return frames, matrices, lenses


def _selected_prims(camera) -> List[str]:
    knob = camera.knob("scene_graph")
    try:
        return _SELECTED_PRIM_RE.findall(knob.toScript()) if knob is not None else []
    except Exception:
        return []


def _camera_prim(stage, selected, UsdGeom):
    """The camera the node had selected in this file, else its only camera."""
    cameras = [p for p in stage.Traverse() if p.IsA(UsdGeom.Camera)]
    if not cameras:
        raise NotBakeable("no camera in the file")
    for prim in cameras:
        if str(prim.GetPath()) in selected:
            return prim
    if len(cameras) > 1:
        raise NotBakeable(f"{len(cameras)} cameras in the file, none selected")
    return cameras[0]


def _sample_times(prim) -> List[float]:
    """Authored time samples of the camera and of the transforms above it."""
    times = set()
    current = prim
    while current and current.IsValid() and not current.IsPseudoRoot():
        for attribute in current.GetAttributes():
            if current == prim or attribute.GetName().startswith("xformOp"):
                times.update(attribute.GetTimeSamples())
        current = current.GetParent()
    return sorted(times)


def _decompose(matrices) -> Tuple[List[tuple], List[tuple]]:
    """(rotate XYZ in degrees, scaling) per matrix. Rotations are kept
    continuous from one frame to the next — the same orientation has many
    Euler triples, and a 360 degree jump between two keys would spin the
    camera on sub-frame samples (motion blur)."""
    from pxr import Gf
    x, y, z = Gf.Vec3d(1, 0, 0), Gf.Vec3d(0, 1, 0), Gf.Vec3d(0, 0, 1)
    rotations, scales = [], []
    for matrix in matrices:
        rows = [Gf.Vec3d(*matrix.GetRow3(i)) for i in range(3)]
        lengths = [row.GetLength() for row in rows]
        if min(lengths) < 1e-9:
            raise NotBakeable("degenerate transform (zero scale)")
        for a, b in ((0, 1), (0, 2), (1, 2)):
            if abs(Gf.Dot(rows[a], rows[b])) > 1e-6 * lengths[a] * lengths[b]:
                raise NotBakeable("sheared transform")
        if matrix.GetDeterminant3() < 0:
            raise NotBakeable("mirrored transform")
        rz, ry, rx = Gf.Matrix4d(matrix).RemoveScaleShear().ExtractRotation().Decompose(z, y, x)
        angles = (rx, ry, rz)
        rotations.append(_closest_euler(rotations[-1], angles) if rotations else angles)
        scales.append(tuple(lengths))
    return rotations, scales


def _closest_euler(previous, angles) -> tuple:
    """The triple equivalent to `angles` nearest to `previous`: (x, y, z)
    and (x+180, 180-y, z+180) are the same rotation, as is any multiple of
    360 on an angle."""
    best = None
    for candidate in (angles, (angles[0] + 180.0, 180.0 - angles[1], angles[2] + 180.0)):
        unwrapped = tuple(a + 360.0 * round((p - a) / 360.0) for a, p in zip(candidate, previous))
        distance = sum(abs(a - p) for a, p in zip(unwrapped, previous))
        if best is None or distance < best[0]:
            best = (distance, unwrapped)
    return best[1]


def _write_knobs(camera, path, frames, matrices, rotations, scales, lenses):
    camera["read_from_file"].setValue(False)   # first: nothing may reload the file over what follows
    camera["file"].setValue(path)
    camera["rot_order"].setValue("XYZ")
    camera["xform_order"].setValue("SRT")
    camera["useMatrix"].setValue(False)
    translations = [tuple(matrix.ExtractTranslation()) for matrix in matrices]
    _set(camera["translate"], frames, translations)
    _set(camera["rotate"], frames, rotations)
    _set(camera["scaling"], frames, scales)
    for name, rest in (("skew", (0.0, 0.0, 0.0)), ("pivot", (0.0, 0.0, 0.0)), ("uniform_scale", (1.0,))):
        _set(camera[name], None, [rest])
    for name, read in _LENS:
        _set(camera[name], frames, [(read(lens),) for lens in lenses])


def _set(knob, frames, rows):
    """One key per frame and per field (`rows`: one tuple of fields per
    frame), or plain values when `frames` is None."""
    knob.clearAnimated()   # previous keys and expressions
    columns = list(zip(*rows))
    if frames is None:
        knob.fromScript(" ".join("%.10g" % column[0] for column in columns))
    else:
        knob.fromScript(" ".join("{curve x%d %s}" % (frames[0], " ".join("%.10g" % v for v in column))
                                 for column in columns))


def _verify(camera, frames, matrices):
    """Nuke's own evaluation of the knobs must give the file's transform on
    every frame: catches any convention this module would get wrong."""
    world = camera["world_matrix"]
    for index, matrix in enumerate(matrices):
        frame = frames[index] if frames else nuke.frame()
        for row in range(4):
            for column in range(4):
                expected = matrix[column][row]   # USD stores row vectors, the knob column vectors
                got = world.getValueAt(frame, row * 4 + column)
                if abs(got - expected) > 1e-3 + 1e-5 * abs(expected):
                    raise NotBakeable(f"knobs don't reproduce the file's transform at frame {frame} "
                                      f"({got:.6f} for {expected:.6f})")


# ---------------------------------------------------------------------------
# A camera reading its file: do its knobs hold that file's camera?
# ---------------------------------------------------------------------------

_CAMERA_CLASSES = ("Camera", "Camera2", "Camera3", "Camera4")
_TRANSLATION = (3, 7, 11)       # `matrix` knob fields (row * 4 + column) of the translation
_VERSION_DIR_RE = re.compile(r"^v\d{3,4}$", re.IGNORECASE)
# Knobs the comparison reads: a change of any of them invalidates a cached answer.
_COMPARED = _TRANSFORM + ("rot_order", "xform_order", "useMatrix", "matrix", "scene_graph") + tuple(
    name for name, _ in _LENS)
_sync_cache = {}


def _tolerance(expected: float) -> float:
    return 1e-3 + 1e-5 * abs(expected)      # same as _verify()


@dataclass
class Mismatch:
    """Where the knobs and the file part: the first frame that differs
    (`detail`) and the span of the frames that do."""
    detail: str
    first: int
    last: int
    frames: int
    total: int

    def __str__(self):
        if self.total > 1 and self.frames == self.total:
            return f"{self.detail} (every frame)"
        if self.frames == 1:
            return self.detail
        if self.frames == self.last - self.first + 1:
            return f"{self.detail} (frames {self.first}-{self.last})"
        return f"{self.detail} ({self.frames} frames between {self.first} and {self.last})"


@dataclass
class OutOfSync:
    path: str
    mismatch: Mismatch
    held: Optional[str]     # version folder whose camera the knobs hold, None: none of them

    def __str__(self):
        holds = (f"the knobs hold {self.held}'s camera" if self.held
                 else "the knobs hold none of its versions' camera")
        return f"not the camera of {os.path.basename(self.path)}: {self.mismatch}; {holds}"


def read_file(camera) -> Optional[str]:
    """USD file a camera node loads into its knobs (`read from file` on),
    None for anything else."""
    try:
        if camera.Class() not in _CAMERA_CLASSES:
            return None
        gate = camera.knob("read_from_file")
        if gate is None or not gate.value() or camera.knob("file") is None:
            return None
        path = nuke.filename(camera) or camera["file"].value()
    except Exception:
        return None
    path = (path or "").replace("\\", "/")
    return path if path.lower().endswith(_USD_EXTENSIONS) else None


def file_mismatch(camera, path: str) -> Optional[Mismatch]:
    """How the camera held in the knobs differs from the camera of `path`,
    None when they are the same. Compared on every frame of the file, with
    bake_file()'s tolerance: the transform Nuke evaluates from the knobs
    (local `matrix`: a parent Axis is not the file's business), then the
    lens. Raises NotBakeable for a file not read the way bake_file reads it."""
    frames, matrices, lenses = _read_usd(path.replace("\\", "/"), _selected_prims(camera))
    local = camera["matrix"]
    found, first, last, count = None, None, None, 0
    for index, matrix in enumerate(matrices):
        frame = frames[index] if frames else int(nuke.frame())
        detail = _frame_difference(camera, local, frame, matrix, lenses[index])
        if detail is None:
            continue
        count += 1
        last = frame
        if found is None:
            found, first = detail, frame
    if found is None:
        return None
    return Mismatch(found, first, last, count, len(matrices))


def _frame_difference(camera, local, frame, matrix, lens) -> Optional[str]:
    """What differs on one frame: position, then orientation / scale, then
    the lens knobs. None when nothing does."""
    got = [local.getValueAt(frame, index) for index in range(16)]
    expected = [matrix[index % 4][index // 4] for index in range(16)]   # USD rows <-> knob columns
    if any(abs(got[i] - expected[i]) > _tolerance(expected[i]) for i in _TRANSLATION):
        offset = math.sqrt(sum((got[i] - expected[i]) ** 2 for i in _TRANSLATION))
        return f"position off by {offset:.4g} at frame {frame}"
    if any(abs(g - e) > _tolerance(e) for g, e in zip(got, expected)):
        return f"orientation differs at frame {frame}"
    for name, read in _LENS:
        value, wanted = camera[name].getValueAt(frame), read(lens)
        if abs(value - wanted) > _tolerance(wanted):
            return f"{name} {value:.4g} instead of {wanted:.4g} at frame {frame}"
    return None


def held_version(camera, path: str) -> Optional[str]:
    """Version folder next to the one of `path` ('v002') whose camera the
    knobs hold, newest first; None when they hold none of them."""
    folder = os.path.dirname(path.replace("\\", "/"))
    parent, current = os.path.dirname(folder), os.path.basename(folder)
    if not _VERSION_DIR_RE.match(current):
        return None
    try:
        names = sorted((n for n in os.listdir(parent) if _VERSION_DIR_RE.match(n) and n != current),
                       key=version_int, reverse=True)
    except OSError:
        return None
    for name in names:
        candidate = _usd_file(os.path.join(parent, name))
        if candidate is None:
            continue
        try:
            if file_mismatch(camera, candidate) is None:
                return name
        except NotBakeable:
            continue
    return None


def _usd_file(folder: str) -> Optional[str]:
    try:
        names = sorted(n for n in os.listdir(folder) if n.lower().endswith(_USD_EXTENSIONS))
    except OSError:
        return None
    return os.path.join(folder, names[0]).replace("\\", "/") if names else None


def out_of_sync(camera) -> Optional[OutOfSync]:
    """A camera with `read from file` whose knobs hold another camera than
    its file — what Nuke would load over them the first time the camera's
    properties panel exists. None when they agree, and for files that can't
    be compared (not USD, unreadable, outside what bake_file reads). Cached
    on the node, the file and the compared knobs: the Loader asks on every
    refresh."""
    path = read_file(camera)
    if path is None:
        return None
    try:
        stat = os.stat(path)
        knobs = "\n".join(camera[name].toScript() for name in _COMPARED if camera.knob(name) is not None)
        key = (camera.fullName(), path, stat.st_mtime, stat.st_size, hash(knobs))
    except Exception:
        return None
    if key in _sync_cache:
        return _sync_cache[key]
    try:
        mismatch = file_mismatch(camera, path)
        result = None if mismatch is None else OutOfSync(path, mismatch, held_version(camera, path))
    except NotBakeable as reason:
        print(f"[cameras] {camera.name()}: not compared with {os.path.basename(path)} ({reason})")
        result = None
    if len(_sync_cache) > 64:
        _sync_cache.clear()
    _sync_cache[key] = result
    return result


def _snapshot(camera) -> dict:
    knobs = ("file",) + _SETTINGS + _TRANSFORM + tuple(name for name, _ in _LENS)
    return {name: camera[name].toScript() for name in knobs if camera.knob(name) is not None}


def _restore(camera, saved: dict):
    for name, script in saved.items():
        try:
            camera[name].clearAnimated()
        except Exception:
            pass
        try:
            camera[name].fromScript(script)
        except Exception as e:
            print(f"[cameras] {camera.name()}.{name} not restored: {e}")


# ---------------------------------------------------------------------------
# Nuke's own import
# ---------------------------------------------------------------------------

def load_file(camera, path: str = None, frame_rate: float = None) -> bool:
    """Have Nuke load a camera file into the node: `path` (and `frame_rate`)
    when given, else the node's current file again. False when it could not
    (no GUI): the knobs are set, the camera data is not."""
    gui = bool(getattr(nuke, "GUI", False))
    # `suppress_dialog` skips Nuke's "destroy the current camera data?"
    # question; silent_popups stays as a safety net.
    with silent_popups(f"camera file {camera.name()}", linger_ms=500):
        suppress = camera.knob("suppress_dialog")
        asks = suppress.value() if suppress is not None else None
        if suppress is not None:
            suppress.setValue(True)
        opened = _open_panel(camera) if gui else False
        try:
            if path is not None:
                camera["file"].setValue(path.replace("\\", "/"))
            if camera.knob("read_from_file") is not None:
                camera["read_from_file"].setValue(True)
            if frame_rate is not None and camera.knob("frame_rate") is not None:
                camera["frame_rate"].setValue(frame_rate)
            reload = camera.knob("reload") or camera.knob("reload_link")
            if reload is not None:
                reload.execute()
        finally:
            if opened:
                camera.hideControlPanel()
            if suppress is not None:
                suppress.setValue(asks)
    if not gui:
        print(f"[cameras] {camera.name()}: file set, camera data not loaded (Nuke only loads it in the GUI)")
        return False
    print(f"[cameras] {camera.name()}: camera loaded from {camera['file'].value()}")
    return True


def _open_panel(node) -> bool:
    """Make sure the node's properties panel exists. True when this call
    opened it; False when it exists already (Node.shown() stays True once a
    panel was opened, even closed since)."""
    try:
        if node.shown():
            return False
        node.showControlPanel()
        return True
    except Exception as e:
        print(f"[cameras] properties panel of {node.name()} not opened: {e}")
        return False
