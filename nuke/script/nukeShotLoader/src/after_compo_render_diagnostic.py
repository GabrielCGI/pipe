import os, json
import nuke
import module_precomp as mp


def _is_precomp_write(node):
    try:
        if node.Class() != "Write":
            return False
        if 'tag' not in node.knobs():
            return False
        return (node['tag'].value() or "").strip() == "PrecompWrite"
    except Exception:
        return False


def _find_switch_for(precomp_write):
    pw_full = precomp_write.fullName()
    for node in nuke.allNodes(recurseGroups=True):
        knobs = node.knobs()
        if node.Class() != "Switch" and 'which' not in knobs and 'which_custom' not in knobs:
            continue
        try:
            n_inputs = node.inputs()
        except Exception:
            n_inputs = 2
        for i in range(n_inputs):
            try:
                n = node.input(i)
            except Exception:
                continue
            seen = set()
            while n is not None and n.Class() == "Dot" and n.fullName() not in seen:
                seen.add(n.fullName())
                try:
                    n = n.input(0)
                except Exception:
                    n = None
            if n is not None and n.fullName() == pw_full:
                return node
    return None


def _read_switch_which(sw):
    knobs = sw.knobs()
    knob_name = 'which_custom' if 'which_custom' in knobs else 'which'
    return int(sw[knob_name].value())


def _knob_value(node, name):
    try:
        return node[name].value() if name in node.knobs() else None
    except Exception:
        return None


def _read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def _diagnose():
    compo = nuke.thisNode()
    print("=" * 70)
    print(f"[after_compo_render_diagnostic] Compo write: {compo.name()}")
    print(f"  file : {compo['file'].value() if 'file' in compo.knobs() else '(no file knob)'}")

    precomps = [n for n in nuke.allNodes("Write", recurseGroups=True) if _is_precomp_write(n)]
    if not precomps:
        print("  (no PrecompWrite nodes found in scene)")
        print("=" * 70)
        return

    print(f"  {len(precomps)} PrecompWrite(s) found")
    print("-" * 70)

    for pw in sorted(precomps, key=lambda n: n.fullName()):
        identifier = _knob_value(pw, 'identifier')
        version = _knob_value(pw, 'versions')
        renderpath = _knob_value(pw, 'renderpath') or ""
        folder = os.path.dirname(renderpath) if renderpath else ""

        state_path = os.path.join(folder, "render_state.json") if folder else ""
        ref_path = os.path.join(folder, "cache_ref.json") if folder else ""

        state = _read_json(state_path) if state_path and os.path.exists(state_path) else None
        ref = _read_json(ref_path) if ref_path and os.path.exists(ref_path) else None

        render_done = state.get("Render_Done") if isinstance(state, dict) else None
        ref_hash = ref.get("ref_hash") if isinstance(ref, dict) else None

        try:
            live_hash = mp.upstream_hash(pw)
        except Exception as e:
            live_hash = f"<error: {e}>"

        sw = _find_switch_for(pw)
        if sw is None:
            sw_name = "(none)"
            which_val = None
        else:
            sw_name = sw.name()
            try:
                which_val = _read_switch_which(sw)
            except Exception as e:
                which_val = f"<error: {e}>"

        if which_val == 0:
            verdict = "CACHED"
        elif isinstance(which_val, int):
            verdict = "LIVE"
        else:
            verdict = "UNKNOWN"

        hash_match = (ref_hash is not None and ref_hash == live_hash)

        print(f"[{pw.name()}] id=precomp_{identifier} v{int(version) if isinstance(version, (int, float)) else version}")
        print(f"  switch          : {sw_name}  which={which_val}  -> {verdict}")
        print(f"  folder          : {folder}")
        print(f"  render_state    : {state_path if state_path else '(no folder)'}")
        print(f"                    exists={bool(state)}  Render_Done={render_done}")
        print(f"  cache_ref       : {ref_path if ref_path else '(no folder)'}")
        print(f"                    exists={bool(ref)}  ref_hash={ref_hash}")
        print(f"  live hash       : {live_hash}")
        print(f"  hash match      : {hash_match}")
        if not hash_match:
            print(f"  --- upstream_hash dump (farm side) for {pw.name()} ---")
            try:
                for line in mp.upstream_hash_dump(pw):
                    print(f"    {line}")
            except Exception as e:
                print(f"    <dump failed: {e}>")
            print(f"  --- end dump ---")
        print("-" * 70)

    print("=" * 70)


try:
    _diagnose()
except Exception as e:
    print(f"[after_compo_render_diagnostic] failed: {e}")
