import hou
# ─────────────────────────────────────────────────────────────
#  1. Récupérer la sélection dans le Scene Graph
# ─────────────────────────────────────────────────────────────

viewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
if not viewer:
    raise RuntimeError("Aucun Scene Viewer trouvé.")

sg_sel = viewer.currentSceneGraphSelection()
if not sg_sel:
    raise RuntimeError("Aucun prim sélectionné dans le Scene Graph.")

prim_paths = list(sg_sel)
print(f"[KarmaBaker] {len(prim_paths)} prim(s) sélectionné(s).")


# ─────────────────────────────────────────────────────────────
#  2. Trouver le réseau LOP courant
# ─────────────────────────────────────────────────────────────

lop_net = viewer.currentNode().parent()


# ─────────────────────────────────────────────────────────────
#  3. Créer un karmatexturebaker + usdrender_rop par prim
# ─────────────────────────────────────────────────────────────

created = []
for prim_path in prim_paths:
    node_name = prim_path.strip("/").replace("/", "_")

    # Karma Texture Baker
    baker = lop_net.createNode("karmatexturebaker", node_name)
    baker.parm("bakemesh").set(prim_path)
    baker.parm("highmesh").set(prim_path)
    baker.parm("bake_uv").set("uv2")
    baker.parm("bakemode").set("single")       # 3 = single
    baker.parm("missing_normals").set("create")  
    # AOVs
    baker.parm("aov_base_color").set(1) # ON
    baker.parm("aov_Nt").set(0)         # OFF
    baker.parm("aov_Af").set(0)         # OFF

    # USD Render ROP wired to the baker
    rop = lop_net.createNode("usdrender_rop", f"{node_name}_rop")
    rop.parm("rendersettings").set("/Render/karmabake_*")
    rop.setInput(0, baker)

    created.extend([baker, rop])
    print(f"[KarmaBaker] Created '{baker.name()}' + '{rop.name()}' → {prim_path}")

lop_net.layoutChildren(created)
print(f"[KarmaBaker] Done — {len(prim_paths)} pair(s) created.")