import hou
import hdefereval


def bypass_object_merges(nodes):
    object_merges_to_delete = set()

    for node in nodes:
        if node.type().category() != hou.sopNodeTypeCategory():
            continue

        for input_idx, input_node in enumerate(node.inputs()):
            if input_node is None:
                continue
            if input_node.type().name() != "object_merge":
                continue

            objpath = input_node.parm("objpath1").eval()
            if not objpath:
                print(f"[bypass] SKIP {input_node.path()}: objpath1 is empty.")
                continue

            target_node = hou.node(objpath)
            if target_node is None:
                print(f"[bypass] SKIP {input_node.path()}: '{objpath}' does not resolve.")
                continue

            if target_node.parent().path() != node.parent().path():
                print(f"[bypass] SKIP {node.path()} input[{input_idx}]: '{target_node.path()}' is in a different network.")
                continue

            try:
                node.setInput(input_idx, target_node, 0)
                print(f"[bypass] OK  {node.path()} input[{input_idx}]: {input_node.path()} → {target_node.path()}")
                object_merges_to_delete.add(input_node)
            except hou.OperationFailed as e:
                print(f"[bypass] FAIL {node.path()} input[{input_idx}]: {e}")

    for merge_node in object_merges_to_delete:
        try:
            if len(merge_node.outputs()) == 0:
                print(f"[bypass] DELETE {merge_node.path()}")
                merge_node.destroy()
            else:
                print(f"[bypass] KEEP {merge_node.path()}: still has outputs.")
        except hou.OperationFailed as e:
            print(f"[bypass] FAIL deleting {merge_node.path()}: {e}")


def _render_and_restore(rop_node):
    try:
        print(f"[run] Rendering {rop_node.path()} ...")
        with hou.undos.disabler():
            rop_node.render()
        print(f"[run] Render done.")
    except hou.OperationFailed as e:
        print(f"[run] Render FAILED: {e}")
    finally:
        print(f"[run] Restoring network ...")
        hou.undos.performUndo()
        print(f"[run] Network restored.")


def run():
    this_node = hou.pwd()
    path = this_node.parm("procedural_path").eval()
    rop_path = this_node.parm("rop_export").eval()

    subnet = hou.node(path)
    if subnet is None:
        print(f"[run] Node not found: '{path}'")
        return

    rop_node = hou.node(rop_path)
    if rop_node is None:
        print(f"[run] ROP not found: '{rop_path}'")
        return

    nodes = subnet.children()
    print(f"[run] Found {len(nodes)} nodes in {path}")

    with hou.undos.group("Bypass object_merge nodes"):
        bypass_object_merges(nodes)

    # Defer render+undo to after Houdini's outer callback undo group closes
    hdefereval.executeDeferred(_render_and_restore, rop_node)