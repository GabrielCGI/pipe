"""Sanity rules checked before a render is submitted.

A rule looks at the nodes the render depends on (Context.nodes: inputs,
expression links and plain Group internals of the Writes to render) or at
the Writes themselves, returns one Issue per offending node, and can fix
its issues. Order matters: RULES are run first to last.
"""

import os
import re
import shutil
import time
from dataclasses import dataclass
from typing import Callable, List, Optional

import nuke

from ..core.config import Config
from ..precomp.hashing import ContentHasher
from ..scene import cameras

Progress = Optional[Callable[[int, int, str], None]]   # (done, total, what)


@dataclass
class Issue:
    node: object
    detail: str
    data: object = None      # rule-specific payload for the fix


class Context:
    """What a submission renders: the Writes, and every node their renders
    depend on (`nodes`, collected on first use unless given)."""

    def __init__(self, writes, nodes: Optional[List] = None, shot_folder: Optional[str] = None):
        self.writes = list(writes)
        self.shot_folder = shot_folder
        self._nodes, self._given = nodes, nodes is not None

    @property
    def nodes(self) -> List:
        if self._nodes is None:
            self._nodes = involved_nodes(self.writes)
        return self._nodes

    def refresh(self):
        """After a fix changed the graph: collect the nodes again."""
        if not self._given:
            self._nodes = None


def involved_nodes(writes) -> List:
    """Nodes the renders of `writes` depend on, as the precomp hash sees them."""
    hasher = ContentHasher()
    for write in writes:
        hasher.node_hash(write)
    return list(hasher.visited_nodes.values())


class Rule:
    title = ""
    fix_label = "Fix"
    fix_help = ""

    def check(self, context: Context, progress: Progress = None) -> List[Issue]:
        raise NotImplementedError

    def fix(self, issues: List[Issue], context: Context, progress: Progress = None) -> List[str]:
        """Fix `issues`. Returns the failures (one line each), [] when all went well."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 1. Files read outside the network
# ---------------------------------------------------------------------------

_FRAME_TOKEN_RE = re.compile(r"%0?(\d*)d|#+")


def read_path(node) -> Optional[str]:
    """File a node reads (Read, DeepRead, Camera, ReadGeo, Axis...), None for
    nodes that don't read one. Expressions in the knob are resolved."""
    if "write" in node.Class().lower() or node.knob("file") is None:
        return None
    gate = node.knob("read_from_file")
    if gate is not None and not gate.value():
        return None
    try:
        path = nuke.filename(node)
    except Exception:
        path = None
    path = path or node["file"].value()
    return path.replace("\\", "/") if path else None


def is_on_network(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return any(normalized.startswith(root.lower()) for root in Config.NETWORK_ROOTS)


def sequence_files(path: str) -> List[str]:
    """Files on disk behind a Nuke file path ('x.####.exr', 'x.%04d.exr' or
    a single file)."""
    folder, base = os.path.split(path)
    token = _FRAME_TOKEN_RE.search(base)
    if token is None:
        return [path] if os.path.isfile(path) else []
    regex = re.compile("^" + re.escape(base[:token.start()]) + r"-?\d+" + re.escape(base[token.end():]) + "$",
                       re.IGNORECASE)
    try:
        return sorted(os.path.join(folder, name) for name in os.listdir(folder) if regex.match(name))
    except OSError:
        return []


class OffNetworkPaths(Rule):
    title = "Files read outside the network"
    fix_label = "Fix: copy to the shot and repath"
    fix_help = ("The farm only reads " + ", ".join(Config.NETWORK_ROOTS) + ". Fix copies the files to "
                "<shot>/" + Config.LOCAL_COPY_PATH + "/<node>/ and points the nodes at the copies.")

    def check(self, context, progress=None):
        issues = []
        for node in context.nodes:
            path = read_path(node)
            if path and not is_on_network(path):
                issues.append(Issue(node, path, path))
        return issues

    def fix(self, issues, context, progress=None):
        if not context.shot_folder:
            return ["No shot detected for this script: nowhere to copy the files to."]
        jobs, failures = [], []
        for issue in issues:
            files = sequence_files(issue.data)
            if files:
                jobs.append((issue, files))
            else:
                failures.append(f"{issue.node.fullName()}: no file found at {issue.data}")
        total, done = sum(len(files) for _, files in jobs), 0
        for issue, files in jobs:
            node = issue.node
            folder = os.path.join(context.shot_folder, *Config.LOCAL_COPY_PATH.split("/"),
                                  re.sub(r"[^\w.-]", "_", node.name()))
            try:
                os.makedirs(folder, exist_ok=True)
                for source in files:
                    target = os.path.join(folder, os.path.basename(source))
                    if not _same_file(source, target):
                        shutil.copy2(source, target)
                    done += 1
                    if progress:
                        progress(done, total, f"Copying {node.name()}  {done}/{total}")
                node["file"].setValue(os.path.join(folder, os.path.basename(issue.data)).replace("\\", "/"))
                print(f"[sanity] {node.fullName()}: {len(files)} file(s) copied to {folder}")
            except Exception as e:
                failures.append(f"{node.fullName()}: {type(e).__name__}: {e}")
        return failures


def _same_file(source, target) -> bool:
    try:
        a, b = os.stat(source), os.stat(target)
    except OSError:
        return False
    return a.st_size == b.st_size and int(a.st_mtime) == int(b.st_mtime)


# ---------------------------------------------------------------------------
# 2. Cameras holding another camera than their file
# ---------------------------------------------------------------------------

class StaleCameras(Rule):
    title = "Cameras out of sync with their file"
    fix_label = "Fix: bake the file's camera"
    fix_help = ("A camera with 'read from file' renders from its knobs, in the viewer and on the farm. Nuke copies "
                "the file into them only when the camera's properties panel exists: after a version change they "
                "can keep an older camera (or the scene preset's) until the panel gets opened — the camera then "
                "changes and every cache downstream goes Live. Fix bakes the file's camera into the knobs "
                "('read from file' off): the render uses it, and opening the panel no longer changes anything. "
                "The precomps downstream are rendered again once.")

    def check(self, context, progress=None):
        candidates = [node for node in context.nodes if cameras.read_file(node)]
        issues = []
        for index, node in enumerate(candidates):
            if progress:
                progress(index, len(candidates), f"Cameras: {node.name()}  ({index + 1}/{len(candidates)})")
            report = cameras.out_of_sync(node)
            if report is not None:
                issues.append(Issue(node, str(report), report.path))
        return issues

    def fix(self, issues, context, progress=None):
        failures = []
        for index, issue in enumerate(issues):
            camera = issue.node
            if progress:
                progress(index, len(issues), f"Baking {camera.name()}  ({index + 1}/{len(issues)})")
            try:
                try:
                    cameras.bake_file(camera, issue.data)
                except cameras.NotBakeable as reason:   # Nuke's own import, GUI only
                    if not cameras.load_file(camera):
                        failures.append(f"{camera.fullName()}: not baked ({reason}), and Nuke loads camera "
                                        "files in the GUI only")
                        continue
                print(f"[sanity] {camera.fullName()}: camera of {os.path.basename(issue.data)} now in its knobs")
            except Exception as e:
                failures.append(f"{camera.fullName()}: {type(e).__name__}: {e}")
        return failures


# ---------------------------------------------------------------------------
# 3. Uppercase identifiers in Expression / DeepExpression
# ---------------------------------------------------------------------------
# Nuke resolves an uppercase channel letter inconsistently: on the first
# evaluation after a script load `B` reads depth.Z and `A` reads 0, so the
# first frame of every farm task renders wrong while the viewer looks right.

_IDENTIFIER_RE = re.compile(r"[A-Za-z_]\w*")
_INNER_TCL_RE = re.compile(r"\[[^\[\]]*\]")


def expression_knobs(node) -> List:
    """The per-pixel expression knobs of an Expression / DeepExpression."""
    names = [f"temp_expr{i}" for i in range(4)]
    if node.Class() == "Expression":
        names += [f"expr{i}" for i in range(4)]
    else:  # DeepExpression: one knob per channel, named like the channel
        names += [name for name in node.knobs() if "." in name]
    return [node[name] for name in names if node.knob(name) is not None]


def _text(knob) -> str:
    try:
        return knob.getText() or ""
    except Exception:
        return str(knob.value() or "")


def uppercase_identifiers(node, text: str) -> List:
    """(start, end, token) of the identifiers of `text` written with capitals
    that Nuke would read as channels. Left alone: node / knob references
    ('Grade1.white', 'parent.Axis1.matrix'), functions, TCL brackets, the
    node's temp variables and its own knobs."""
    masked = text
    while True:  # blank out [tcl ...] blocks, innermost first
        blanked = _INNER_TCL_RE.sub(lambda m: " " * len(m.group()), masked)
        if blanked == masked:
            break
        masked = blanked
    temps = {(node[f"temp_name{i}"].value() or "").strip() for i in range(4) if node.knob(f"temp_name{i}") is not None}
    found = []
    for match in _IDENTIFIER_RE.finditer(masked):
        token, (start, end) = match.group(), match.span()
        if token == token.lower() or token in temps:
            continue
        if start and (masked[start - 1] == "." or masked[start - 1].isdigit()):  # reference tail, 1E5
            continue
        if masked[end:].lstrip()[:1] in (".", "("):  # node reference, function
            continue
        if node.knob(token) is not None:
            continue
        found.append((start, end, token))
    return found


class UppercaseExpressions(Rule):
    title = "Uppercase channels in Expression nodes"
    fix_label = "Fix: lowercase them"
    fix_help = ("Nuke reads an uppercase channel (B, A...) wrongly on the first frame of each farm task. "
                "Fix writes them in lowercase; node and knob references are left untouched.")

    def check(self, context, progress=None):
        issues = []
        for node in context.nodes:
            if node.Class() not in ("Expression", "DeepExpression"):
                continue
            hits = {}
            for knob in expression_knobs(node):
                tokens = uppercase_identifiers(node, _text(knob))
                if tokens:
                    hits[knob.name()] = sorted({token for _, _, token in tokens})
            if hits:
                detail = "   ".join(f"{name}: {' '.join(tokens)}" for name, tokens in hits.items())
                issues.append(Issue(node, detail, list(hits)))
        return issues

    def fix(self, issues, context, progress=None):
        failures = []
        for issue in issues:
            node = issue.node
            try:
                for name in issue.data:
                    knob, text = node[name], _text(node[name])
                    for start, end, token in reversed(uppercase_identifiers(node, text)):
                        text = text[:start] + token.lower() + text[end:]
                    knob.setValue(text)
                print(f"[sanity] {node.fullName()}: uppercase identifiers lowercased ({issue.detail})")
            except Exception as e:
                failures.append(f"{node.fullName()}: {type(e).__name__}: {e}")
        return failures


# ---------------------------------------------------------------------------
# 4. Knob expressions in error
# ---------------------------------------------------------------------------
# An expression Nuke cannot evaluate (node or knob renamed / deleted, typo)
# silently returns 0, in the viewer as on the farm. Nuke has no API telling
# so: the expression is evaluated again through TCL in the node's context,
# which raises. That context has no "current knob field", so three guards
# keep a valid expression from being reported (its fix deletes it):
#   - a name that exists is never an error ('translate' in the x field of a
#     Transform means translate.x; TCL alone can't pick the field);
#   - the knob itself must evaluate to 0 on every sampled frame;
#   - the node must be reachable by its name (a child node named like a knob
#     of its group is not: TCL would land in the group).

_NOT_NAMED_RE = re.compile(r'^Nothing is named "(.+)"$')


def _tcl_in(node, script: str, **variables) -> str:
    """Run `script` in the node's context; `variables` are TCL variables it
    reads ($name), so their text never needs quoting."""
    for name, value in variables.items():
        nuke.tcl("set", name, value)
    return nuke.tcl("in", node.fullName(), script)


def expression_error(node, expression: str) -> Optional[str]:
    """Why `expression` can't be evaluated in `node`, None when it can."""
    for _ in range(12):  # each pass settles one multi-field knob reference
        try:
            _tcl_in(node, "expression $__sl_expr", __sl_expr=expression)
            return None
        except RuntimeError as e:
            message = str(e)
        named = _NOT_NAMED_RE.match(message)
        if named is None:
            return message
        name = named.group(1)
        try:
            exists = _tcl_in(node, "exists $__sl_name", __sl_name=name) == "1"
        except RuntimeError:
            exists = False
        if not exists:
            return message
        settled = re.sub(r"(?<![\w.])" + re.escape(name) + r"(?![\w.(])", "0", expression)
        if settled == expression:
            break
        expression = settled
    return None  # not proven wrong


def _sample_frames() -> List[int]:
    """First, last and current frame — the current one only inside the
    script's range: a frame never rendered can cost a whole upstream
    validation (measured: one `width` expression, 16 s at frame 0)."""
    root = nuke.root()
    first, last = int(root["first_frame"].value()), int(root["last_frame"].value())
    current = int(nuke.frame())
    return sorted({first, last} | ({current} if first <= current <= last else set()))


# Reading what an expression points at can need a whole upstream validated
# on a cold tree (one gizmo knob: 16 s measured in a production comp). What
# can't hold a broken reference is replaced by 1 before a first check: the
# terms that read the input (width, bbox.x...), and the references to knobs
# of nodes that exist (Node.knob, parent.knob, root.knob). The expression is
# evaluated as is only when that first check fails.
_INPUT_TERMS_RE = re.compile(r"(?<![\w.$])(?:input\d*\.)?(?:width|height|pixel_aspect|(?:bbox|format)\.\w+)(?![\w(])")
_DOTTED_RE = re.compile(r"(?<![\w.$])[A-Za-z_]\w*(?:\.\w+)+(?![\w(])")


def _child(group, name):
    try:
        return nuke.toNode(f"{group.fullName()}.{name}") if hasattr(group, "nodes") else None
    except Exception:
        return None


def _reference_owner(node, name):
    """The node `name` designates in an expression of `node`: a node of its
    own group — and, for a group's own knobs, of the group itself. None
    otherwise (left to Nuke's evaluation)."""
    full = node.fullName()
    group = full.rsplit(".", 1)[0] if "." in full else None
    if name == "this":
        return node
    if name == "root":
        return nuke.root()
    if name == "parent":
        return nuke.toNode(group) if group else nuke.root()
    return _child(node, name) or nuke.toNode(f"{group}.{name}" if group else name)


def _settle_reference(node, dotted: str) -> str:
    """'1' for 'Node[.Child...].knob[.field]' when the node and its knob
    exist, `dotted` unchanged otherwise."""
    parts = dotted.split(".")
    owner, index = _reference_owner(node, parts[0]), 1
    while owner is not None and index < len(parts) - 1:
        child = _child(owner, parts[index])
        if child is None:
            break
        owner, index = child, index + 1
    if owner is None or len(parts) - index > 2 or owner.knob(parts[index]) is None:
        return dotted
    return "1"


def settled_expression(node, expression: str) -> str:
    """`expression` with what can't hold a broken reference replaced by 1."""
    def settle(match):
        if match.string[:match.start()].rstrip().endswith(("value", "knob")):
            return match.group(0)   # a TCL [value Node.knob]: the path is text there, not a number
        try:
            return _settle_reference(node, match.group(0))
        except Exception:
            return match.group(0)
    return _DOTTED_RE.sub(settle, _INPUT_TERMS_RE.sub("1", expression))


def broken_expressions(node, frames) -> List[tuple]:
    """(knob name, field index, 'knob.field', expression, error) of the
    expressions of `node` that can't be evaluated."""
    try:
        if "{" not in node.writeKnobs(nuke.WRITE_NON_DEFAULT_ONLY | nuke.TO_SCRIPT):  # no expression, no curve
            return []
        if nuke.toNode(node.fullName()) != node:
            return []
    except Exception:
        return []
    found = []
    for name, knob in node.knobs().items():
        has_expression = getattr(knob, "hasExpression", None)
        try:
            if has_expression is None or not has_expression():
                continue
            for index in range(knob.arraySize()):
                curve = knob.animation(index) if knob.hasExpression(index) else None
                if curve is None:
                    continue
                expression = curve.expression()
                settled = settled_expression(node, expression)
                if settled != expression:
                    if expression_error(node, settled) is None:
                        continue
                elif any(curve.evaluate(frame) for frame in frames):
                    continue
                error = expression_error(node, expression)
                if error:
                    found.append((name, index, curve.knobAndFieldName(), curve.expression(), error))
        except Exception:
            continue
    return found


class ExpressionErrors(Rule):
    title = "Knob expressions in error"
    fix_label = "Fix: remove these expressions"
    fix_help = ("An expression Nuke can't evaluate (a node or a knob that no longer exists, a typo) silently "
                "returns 0, in the viewer as on the farm. Fix removes it (No animation): the knob keeps that 0.")

    def check(self, context, progress=None):
        frames = _sample_frames()
        issues, nodes = [], context.nodes
        for index, node in enumerate(nodes):
            if progress and index % 500 == 0:
                progress(index, len(nodes), f"Expressions: {index}/{len(nodes)} nodes")
            broken = broken_expressions(node, frames)
            if broken:
                detail = "\n      ".join(f"{field}: {expression}   ({error})" for _, _, field, expression, error in broken)
                issues.append(Issue(node, detail, [(name, index) for name, index, _, _, _ in broken]))
        return issues

    def fix(self, issues, context, progress=None):
        failures = []
        for issue in issues:
            node = issue.node
            try:
                for name, index in issue.data:
                    node[name].clearAnimated(index)
                print(f"[sanity] {node.fullName()}: expression removed from "
                      + ", ".join(f"{name}[{index}]" for name, index in issue.data))
            except Exception as e:
                failures.append(f"{node.fullName()}: {type(e).__name__}: {e}")
        return failures


# ---------------------------------------------------------------------------
# 5. Bounding box of the rendered Writes
# ---------------------------------------------------------------------------

_SLOW_MEASURE_SECONDS = 1.0
_TRANSPARENT = ("Dot", "NoOp")      # same bounding box as their input


def _disabled(node) -> bool:
    knob = node.knob("disable")
    return knob is not None and bool(knob.value())


def clamped_box(node) -> Optional[tuple]:
    """(width, height) of the bounding box `node` outputs when its knobs
    alone tell it — a Crop (not one intersecting its input's box: smaller),
    or a Reformat to a format that doesn't preserve the bounding box,
    possibly behind Dots — None when only Nuke can tell."""
    while node is not None and (node.Class() in _TRANSPARENT or _disabled(node)):
        node = node.input(0)
    if node is None:
        return None
    try:
        if node.Class() == "Crop" and not node["intersect"].value():
            x, y, r, t = node["box"].value()
            return r - x, t - y
        if node.Class() == "Reformat" and node["type"].value() == "to format" and not node["pbb"].value():
            fmt = node["format"].value()
            return fmt.width(), fmt.height()
    except Exception:
        pass
    return None


class OversizedBoundingBox(Rule):
    title = "Bounding box before the Writes"
    fix_label = "Fix: add a Crop before the Write"
    fix_help = (f"A bounding box more than {int(Config.BBOX_TOLERANCE * 100)}% larger than the script format "
                "slows the render and bloats the files. Fix inserts a Crop to the format before each Write.")

    def check(self, context, progress=None):
        """A Write behind a Crop is settled from the Crop's knobs. The others
        are measured by Nuke (node.bbox()), which validates their whole
        upstream tree: instant once Nuke has it, seconds when it must open
        the source files first — hence the progress and the timing log."""
        fmt = nuke.root().format()
        width, height = fmt.width(), fmt.height()
        limit = 1.0 + Config.BBOX_TOLERANCE
        issues, total = [], len(context.writes)
        for index, write in enumerate(context.writes):
            if progress:
                progress(index, total, f"Bounding box: {write.name()}  ({index + 1}/{total})")
            source = write.input(0)
            if source is None:
                continue
            box = clamped_box(source)
            if box is None:
                started = time.time()
                try:
                    measured = source.bbox()
                    box = int(measured.w()), int(measured.h())
                except Exception as e:
                    print(f"[sanity] {write.fullName()}: bounding box not readable ({e})")
                    continue
                seconds = time.time() - started
                if seconds > _SLOW_MEASURE_SECONDS:
                    print(f"[sanity] {write.fullName()}: bounding box measured in {seconds:.1f}s "
                          "(Nuke had to validate the tree upstream)")
            box_w, box_h = box
            if box_w > width * limit or box_h > height * limit:
                over = max(box_w / float(width), box_h / float(height)) - 1.0
                issues.append(Issue(write, f"bounding box {int(box_w)}x{int(box_h)} for a {width}x{height} format "
                                           f"(+{over * 100:.0f}%)"))
        return issues

    def fix(self, issues, context, progress=None):
        fmt = nuke.root().format()
        failures = []
        for issue in issues:
            write = issue.node
            try:
                with write.parent():  # the Write may live in a group
                    crop = nuke.nodes.Crop(name=f"Crop_{write.name()}", inputs=[write.input(0)])
                crop["box"].setValue([0, 0, fmt.width(), fmt.height()])
                crop["reformat"].setValue(False)
                crop["crop"].setValue(True)
                crop.setXYpos(write.xpos(), write.ypos() - 30)
                write.setInput(0, crop)
                print(f"[sanity] {write.fullName()}: {crop.name()} inserted (crop to {fmt.width()}x{fmt.height()})")
            except Exception as e:
                failures.append(f"{write.fullName()}: {type(e).__name__}: {e}")
        return failures


RULES = (OffNetworkPaths(), StaleCameras(), UppercaseExpressions(), ExpressionErrors(), OversizedBoundingBox())
