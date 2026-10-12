"""Distribute `render_order` over the Writes upstream of a root Write.

The most upstream Writes render first, the root last. Independent Writes
at the same DAG level share a value so the Illogic Deadline submitter
fork can send them in parallel.
"""

import nuke

from .utils import no_undo, upstream_nodes


def distribute_write_render_order(root="WriteCompo", write_classes=("Write",),
                                  start_order=1, step=1, distinct=False):
    """
    root          : root node (or its name) — rendered last.
    write_classes : node classes to order (e.g. ("Write", "DeepWrite")).
    start_order   : value given to the most upstream level.
    step          : increment between two levels (or two nodes if distinct).
    distinct      : True -> every Write gets a unique value (strict topo order).

    Returns the Writes in render order. Only knobs whose value actually
    changes are touched, outside the undo history (automatic change).
    """
    root_node = nuke.toNode(root) if isinstance(root, str) else root
    if root_node is None:
        raise ValueError(f"Node not found: {root!r}")

    upstream_cache = {}

    def upstream_of(node):
        if node not in upstream_cache:
            upstream_cache[node] = upstream_nodes(node)
        return upstream_cache[node]

    writes = [n for n in upstream_of(root_node) | {root_node} if n.Class() in write_classes]
    if not writes:
        nuke.message(f"No Write node found upstream of {root_node.name()}.")
        return []
    write_set = set(writes)

    levels = {}

    def level(write):
        """Longest chain of Writes upstream of `write`."""
        if write not in levels:
            ancestors = upstream_of(write) & write_set
            levels[write] = 1 + max(level(a) for a in ancestors) if ancestors else 0
        return levels[write]

    ordered = sorted(writes, key=lambda w: (level(w), w.name()))
    targets = [
        (w, start_order + (i if distinct else level(w)) * step)
        for i, w in enumerate(ordered)
    ]
    with no_undo():
        for w, value in targets:
            if w["render_order"].value() != value:
                w["render_order"].setValue(value)

    print(f"[DistributeRenderOrder] Render order upstream of {root_node.name()}:")
    for w, value in targets:
        print(f"[DistributeRenderOrder]   {value:<4d} {w.name()}")
    return ordered


def order_from_upstream(writes, write_classes=("Write",), start_order=1):
    """render_order of Writes that no root Write orders (out-of-stream
    precomps), from their own upstream: each renders right after the last
    Write upstream of it. Writes of `writes` are computed together; any
    other Write upstream keeps its render_order (the one the distribution
    from the Compo Write gave it). Returns the Writes in render order."""
    writes = list(writes)
    wanted = set(writes)
    orders = {}

    def order(write):
        if write not in orders:
            orders[write] = start_order  # cycle guard (expression links)
            upstream = [n for n in upstream_nodes(write) if n.Class() in write_classes]
            orders[write] = 1 + max((order(n) if n in wanted else _render_order(n) for n in upstream),
                                    default=start_order - 1)
        return orders[write]

    ordered = sorted(writes, key=lambda w: (order(w), w.name()))
    with no_undo():
        for w in ordered:
            if w.knob("render_order") is not None and w["render_order"].value() != orders[w]:
                w["render_order"].setValue(orders[w])
    return ordered


def _render_order(write) -> int:
    try:
        return int(write["render_order"].value())
    except Exception:
        return 0
