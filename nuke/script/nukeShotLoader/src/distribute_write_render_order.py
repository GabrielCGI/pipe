"""
distribute_write_render_order.py

Distribue le render_order des nodes Write situes en amont d'un node racine
(par defaut "WriteCompo"), en respectant les dependances du graphe :
les Write les plus en amont rendent en premier, la racine rend en dernier.
"""

import nuke


def distribute_write_render_order(root_name="WriteCompo",
                                  write_classes=("Write",),
                                  start_order=1,
                                  step=1,
                                  distinct=False):
    """
    root_name     : nom du node de depart (racine, rendu en dernier).
    write_classes : classes de nodes a traiter (ex: ("Write", "DeepWrite", "WriteGeo")).
    start_order   : render_order attribue au(x) Write le(s) plus en amont.
    step          : increment entre deux niveaux / deux nodes.
    distinct      : False (defaut) -> les Write independants (meme niveau dans le
                                      DAG) partagent le meme render_order, ce qui
                                      permet a la fork Illogic du submitter
                                      Deadline de les envoyer en parallele.
                    True            -> chaque Write recoit une valeur unique
                                      (ordre topologique strict).
    """
    root = nuke.toNode(root_name)
    if root is None:
        raise ValueError("Node introuvable : %r" % root_name)

    # --- Cache des ensembles "amont" par node -----------------------------
    _upstream_cache = {}

    def upstream_of(node):
        """Tous les nodes strictement en amont de `node` (parcours des inputs)."""
        if node in _upstream_cache:
            return _upstream_cache[node]
        seen = set()
        stack = [node]
        while stack:
            cur = stack.pop()
            for i in range(cur.inputs()):
                inp = cur.input(i)
                if inp is not None and inp not in seen:
                    seen.add(inp)
                    stack.append(inp)
        _upstream_cache[node] = seen
        return seen

    # --- Recupere les Write en amont (racine incluse) ---------------------
    tree = upstream_of(root) | {root}
    writes = [n for n in tree if n.Class() in write_classes]
    if not writes:
        nuke.message("Aucun node Write trouve en amont de %s." % root_name)
        return []

    write_set = set(writes)

    # --- Rang de chaque Write dans le DAG de dependances des Write --------
    #     level(w) = plus longue chaine de Write en amont se terminant a w
    _level = {}

    def level(w):
        if w not in _level:
            anc = upstream_of(w) & write_set          # Write strictement en amont de w
            _level[w] = 0 if not anc else 1 + max(level(a) for a in anc)
        return _level[w]

    # Tri : amont d'abord, puis par nom (resultat deterministe)
    ordered = sorted(writes, key=lambda w: (level(w), w.name()))

    # --- Attribution du render_order (une seule etape d'undo) ------------
    undo = nuke.Undo()
    undo.begin("Distribute Write render order")
    try:
        for i, w in enumerate(ordered):
            value = start_order + (i if distinct else level(w)) * step
            w["render_order"].setValue(value)
    finally:
        undo.end()

    # --- Rapport dans le Script Editor -----------------------------------
    print("[DistributeRenderOrder] Render order distribue en amont de %s :" % root_name)
    for w in ordered:
        print("[DistributeRenderOrder]   %-4d %s" % (int(w["render_order"].value()), w.name()))
    return ordered


if __name__ == "__main__":
    distribute_write_render_order()
