import hou
import json

def normalize_path(path):
    return path.replace("/", "").replace(".", "").replace(":", "").lower()

def get_light_parm_groups(node):
    layout_parm = node.parm("setting_layout")
    if not layout_parm:
        raise RuntimeError("No setting_layout parm found on node.")

    layout      = json.loads(layout_parm.eval())
    light_paths = [entry["prim_path"] for entry in layout]
    light_paths_sorted = sorted(light_paths, key=len, reverse=True)
    groups = {path: [] for path in light_paths}

    for parm in node.spareParms():
        if parm.parmTemplate().tags().get("husd_property_category") != "attribute":
            continue
        parm_name = parm.name()
        stripped  = parm_name[4:] if parm_name.startswith("xn__") else parm_name
        for light_path in light_paths_sorted:
            if stripped.startswith(normalize_path(light_path)):
                groups[light_path].append(parm)
                break

    return groups

def clear_light_transforms(node, light_path):
    """Clear transform delta entry for a given prim path."""
    try:
        from edit import common
    except ImportError:
        print("  [transforms] Could not import 'edit.common' — skipping transform clear.")
        return

    delta_parm = node.parm("delta")
    if delta_parm is None:
        print("  [transforms] No 'delta' parm found — skipping transform clear.")
        return

    deltageo = delta_parm.eval()
    if deltageo is None:
        print(f"  [transforms] Delta geo is empty — nothing to clear for '{light_path}'.")
        return

    deltageo       = deltageo.freeze()
    deltapointdict = common.makeDeltaPointDict(deltageo)
    point          = deltapointdict.get(light_path)

    if point is None:
        print(f"  [transforms] No transform entry found for '{light_path}'.")
        return

    deltageo.deletePoints([point])
    delta_parm.set(deltageo)
    print(f"  [transforms] Cleared transform delta for '{light_path}'.")

def clear_light_overrides(node, light_path):
    groups = get_light_parm_groups(node)

    if light_path not in groups:
        available = "\n  ".join(groups.keys())
        raise ValueError(f"Light '{light_path}' not found. Available:\n  {available}")

    # ── Spare parms ───────────────────────────────────────────
    parms_to_remove = [p for p in groups[light_path]]
    if parms_to_remove:
        print(f"\nRemoving {len(parms_to_remove)} parm(s) on '{light_path}':")
        for p in parms_to_remove:
            print(f"  - {p.description()}")

        ptg = node.parmTemplateGroup()
        tuple_names_seen = set()
        for p in parms_to_remove:
            tuple_names_seen.add(p.tuple().name())
        for tuple_name in tuple_names_seen:
            ptg.remove(tuple_name)
        node.setParmTemplateGroup(ptg)
        print("  Done.")
    else:
        print(f"  Nothing to remove — '{light_path}' has no attribute overrides.")

    # ── Transform delta ───────────────────────────────────────
    clear_light_transforms(node, light_path)

def run():
    selected = hou.selectedNodes()
    if not selected:
        print("No node selected.")
        return

    node   = selected[0]
    groups = get_light_parm_groups(node)

    light_paths = list(groups.keys())
    choice = hou.ui.selectFromList(
        light_paths,
        message="Select a light to clear overrides from:",
        title="Clear Light Overrides",
        num_visible_rows=min(len(light_paths), 10),
    )
    if choice:
        with hou.undos.group("Remove Light Mixer overrides: multiple lights"):
            for idx in choice:
                clear_light_overrides(node, light_paths[idx])
    else:
        print("Cancelled.")