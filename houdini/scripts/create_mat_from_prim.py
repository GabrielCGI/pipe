import hou
import random

# ─────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────

def prim_name(path):
    """Dernier composant d'un USD prim path."""
    return path.rstrip("/").split("/")[-1]

def rand_color():
    return (random.random(), random.random(), random.random())


# ─────────────────────────────────────────────────────────────
#  1. Récupérer la sélection dans le Scene Graph
# ─────────────────────────────────────────────────────────────

viewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
if not viewer:
    raise RuntimeError("Aucun Scene Viewer trouvé.")

sg_sel = viewer.currentSceneGraphSelection()
if not sg_sel:
    raise RuntimeError("Aucun prim sélectionné dans le Scene Graph.")

# sg_sel  →  { hou.LopNode : [prim_path, ...] }
prim_paths = []
source_node = None
for node, paths in sg_sel.items():
    source_node = node
    prim_paths.extend(paths)

if not prim_paths:
    raise RuntimeError("La sélection ne contient aucun chemin de prim.")

print(f"[MatLib] {len(prim_paths)} prim(s) sélectionné(s).")


# ─────────────────────────────────────────────────────────────
#  2. Créer le nœud Material Library dans le réseau LOP
# ─────────────────────────────────────────────────────────────

lop_net = source_node.parent()

matlib = lop_net.createNode("materiallibrary", "matlib_from_selection")
matlib.setInput(0, source_node)

# Place le nœud juste après la source dans le réseau
matlib.setPosition(source_node.position() + hou.Vector2(0, -2))


# ─────────────────────────────────────────────────────────────
#  3. Un shader par prim — même nom, couleur aléatoire
# ─────────────────────────────────────────────────────────────

with hou.undos.group("Create MatLib from selection"):
    for prim_path in prim_paths:
        name = prim_name(prim_path)
        r, g, b = rand_color()

        # --- Subnet = un matériau USD ---
        mat_subnet = matlib.createNode("subnet", name)

        # --- USD Preview Surface (universel Karma/Hydra) ---
        surface = mat_subnet.createNode("usdpreviewsurface", "usdpreviewsurface1")
        surface.parm("diffuseColor1").set(r)
        surface.parm("diffuseColor2").set(g)
        surface.parm("diffuseColor3").set(b)
        surface.parm("roughness").set(0.4)

        # --- Collect : agrège les sorties surface/displacement ---
        collect = mat_subnet.createNode("collect", "collect1")
        collect.setInput(0, surface, 0)   # surface output  →  collect in[0]
        collect.setDisplayFlag(True)
        collect.setRenderFlag(True)

        mat_subnet.layoutChildren()
        print(f"  ✓  {name}  →  rgb({r:.2f}, {g:.2f}, {b:.2f})")

    matlib.layoutChildren()

print(f"\n[MatLib] Terminé — nœud '{matlib.name()}' créé avec {len(prim_paths)} matériau(x).")