"""
depth_sampler.py
Analyse de la plage de profondeur via depth_extra.z et CurveTool.

Pipeline d'analyse (global, une seule fois) :
  1. EdgeExtend  : propage depth_extra.z (sans premultiply, detailAmount=0)
  2. Copy        : depth_extra.z -> rgba.red (acces sans ambiguite)
  3. Expression  : 1/r -> RGB (normalise pour eviter les bugs CurveTool)
  4. CurveTool   : Max Luma Pixel -> min et max de 1/z
  5. Conversion  : min_depth = 1/max(1/z),  max_depth = 1/min(1/z)

Distribution : les cards sont reparties lineairement entre min et max depth.
Un NoOp global contient un slider par calque pour ajustement manuel.
"""

import re
import nuke

FALLBACK_MIN_DEPTH = 100.0
FALLBACK_MAX_DEPTH = 1000.0
DEPTH_GUARD        = 1e-4


def build_depth_pipeline(cg_node, depth_channel="depth_extra.z"):
    """
    Construit le pipeline d'analyse de profondeur (sans executer le CurveTool).

    Le CurveTool sera execute apres la construction complete du graph,
    et son callback afterRender injectera les valeurs dans le NoOp.

    Retourne : nodes_dict (contient 'curve_tool')
    """
    # -- 1. EdgeExtend : propager depth_extra hors des zones transparentes -----
    edge_extend = nuke.nodes.EdgeExtend(inputs=[cg_node])
    edge_extend["channels"].setValue("depth_extra")
    edge_extend["detailAmount"].setValue(0)
    edge_extend["premultiply"].setValue(False)
    edge_extend["label"].setValue("extend\ndepth_extra")

    # -- 2. Copy : depth_extra.z -> rgba.red -----------------------------------
    copy = nuke.nodes.Copy(inputs=[edge_extend, edge_extend])
    copy["from0"].setValue(depth_channel)
    copy["to0"].setValue("rgba.red")
    copy["label"].setValue("{}\n> red".format(depth_channel))

    # -- 3. Expression : 1/z normalisation -> RGB ------------------------------
    expr_inv = nuke.nodes.Expression(inputs=[copy])
    expr_inv["expr0"].setValue("r > {} ? 1.0/r : 0".format(DEPTH_GUARD))
    expr_inv["expr1"].setValue("r > {} ? 1.0/r : 0".format(DEPTH_GUARD))
    expr_inv["expr2"].setValue("r > {} ? 1.0/r : 0".format(DEPTH_GUARD))
    expr_inv["label"].setValue("1/z\nnormalisation")

    # -- 4. Crop : eliminer les pixels noirs hors bounding box -------------------
    # Utiliser le format de l'entree (pas celui du projet)
    input_fmt = expr_inv.format()
    crop = nuke.nodes.Crop(inputs=[expr_inv])
    crop["box"].setValue([0, 0, input_fmt.width(), input_fmt.height()])
    crop["crop"].setValue(False)
    crop["label"].setValue("clip to format")

    # -- 5. CurveTool : Max Luma Pixel (execute apres construction du graph) ---
    curve_tool = nuke.nodes.CurveTool(inputs=[crop])
    curve_tool["operation"].setValue("Max Luma Pixel")
    curve_tool["ROI"].setValue([0, 0, input_fmt.width(), input_fmt.height()])
    curve_tool["label"].setValue("depth\nmin / max")

    return {
        "edge_extend": edge_extend,
        "copy":        copy,
        "expr_inv":    expr_inv,
        "crop":        crop,
        "curve_tool":  curve_tool,
    }


def install_depth_callback(curve_tool, noop_name, knob_names):
    """
    Installe un callback afterRender sur le CurveTool qui, a chaque execution,
    lit les min/max de 1/z et met a jour les sliders du NoOp.

    Cela permet aussi de re-executer le CurveTool manuellement pour
    rafraichir les profondeurs.
    """
    knob_list_str = repr(knob_names)

    script = (
        "ct = nuke.thisNode()\n"
        "frame = nuke.frame()\n"
        "max_inv = ct['maxlumapixvalue'].valueAt(frame, 0)\n"
        "min_inv = ct['minlumapixvalue'].valueAt(frame, 0)\n"
        "guard = {guard}\n"
        "min_d = (1.0 / max_inv) if max_inv > guard else {fb_min}\n"
        "max_d = (1.0 / min_inv) if min_inv > guard else {fb_max}\n"
        "if min_d >= max_d:\n"
        "    min_d, max_d = {fb_min}, {fb_max}\n"
        "ctrl = nuke.toNode('{noop}')\n"
        "if ctrl:\n"
        "    knobs = {knobs}\n"
        "    n = len(knobs)\n"
        "    for i, kn in enumerate(knobs):\n"
        "        t = (i / float(n - 1)) if n > 1 else 0.5\n"
        "        d = max_d - t * (max_d - min_d)\n"
        "        ctrl[kn].setRange(min_d, max_d)\n"
        "        ctrl[kn].setValue(d)\n"
    ).format(
        guard=DEPTH_GUARD,
        fb_min=FALLBACK_MIN_DEPTH,
        fb_max=FALLBACK_MAX_DEPTH,
        noop=noop_name,
        knobs=knob_list_str,
    )

    curve_tool["afterRender"].setValue(script)


def execute_curve_tool(curve_tool):
    """
    Execute le CurveTool apres la construction complete du graph.
    Le callback afterRender se declenche automatiquement et met a jour le NoOp.
    """
    frame = nuke.frame()
    nuke.execute(curve_tool, frame, frame)


def distribute_depths(num_layers, min_depth, max_depth):
    """
    Distribue N calques lineairement entre min et max depth.
    Index 0 = plus loin (haut du PSD = fond).
    Index N-1 = plus proche (bas du PSD = premier plan).

    Retourne une liste de profondeurs.
    """
    if num_layers == 1:
        return [(min_depth + max_depth) / 2.0]

    depths = []
    for i in range(num_layers):
        t = i / float(num_layers - 1)
        depth = max_depth - t * (max_depth - min_depth)
        depths.append(depth)
    return depths


def create_depth_controls(layer_names, depths, min_depth, max_depth,
                          face_cam_rot, vertical_rot,
                          source_name="", source_type="psd",
                          camera_name="", use_stamps=False):
    """
    Cree un unique NoOp avec un slider de profondeur + boutons rotation par calque,
    plus un tab Setup Info pour l'update PSD.

    Retourne : (noop, knob_names)
      knob_names[i] = nom du knob pour le calque i (pour les expressions Card2).
    """
    noop = nuke.nodes.NoOp(name="globalControls")
    noop["label"].setValue("Depth\nControls")
    noop["tile_color"].setValue(0x00FFFFFF)
    noop["note_font"].setValue("Bold")
    noop["note_font_size"].setValue(30)

    tab = nuke.Tab_Knob("depth_tab", "Depth Control")
    noop.addKnob(tab)

    title_html = (
        '<font color=#80dddd size="7">P</font>'
        '<font color=#88dede size="7">i</font>'
        '<font color=#90dede size="7">m</font>'
        '<font color=#98dfdf size="7">p</font>'
        '<font color=#a0dfdf size="7"> </font>'
        '<font color=#a4dfdf size="7">m</font>'
        '<font color=#a8e0e0 size="7">y</font>'
        '<font color=#ace0e0 size="7"> </font>'
        '<font color=#b0e0e0 size="7">D</font>'
        '<font color=#b8e1e1 size="7">M</font>'
        '<font color=#c0e1e1 size="7">P</font>'
    )
    title_knob = nuke.Text_Knob("title", "", title_html)
    noop.addKnob(title_knob)

    scale = nuke.Double_Knob("scale_mult", "Scale multiplicateur")
    scale.setRange(0.5, 5.0)
    scale.setValue(2.0)
    scale.setTooltip("Multiplicateur de taille pour toutes les cards")
    noop.addKnob(scale)

    # -- Boutons globaux rotation (All Vertical / All Face Cam) ----------------
    knob_names = []
    card_names = []
    for layer_name in layer_names:
        knob_name = _safe_knob_name(layer_name)
        knob_names.append(knob_name)
        card_names.append(knob_name + "_card")

    all_v_lines = ["nuke.toNode('{}')['rotate'].setValue([0, {:.6f}, 0])".format(
        cn, vertical_rot[1]) for cn in card_names]
    all_v_script = "; ".join(all_v_lines)

    all_f_lines = ["nuke.toNode('{}')['rotate'].setValue([{:.6f}, {:.6f}, 0])".format(
        cn, face_cam_rot[0], face_cam_rot[1]) for cn in card_names]
    all_f_script = "; ".join(all_f_lines)

    all_v_btn = nuke.PyScript_Knob("all_vertical", "All Vertical", all_v_script)
    noop.addKnob(all_v_btn)

    all_f_btn = nuke.PyScript_Knob("all_face_cam", "All Face Cam", all_f_script)
    all_f_btn.clearFlag(nuke.STARTLINE)
    noop.addKnob(all_f_btn)

    divider = nuke.Text_Knob("divider", "")
    noop.addKnob(divider)

    # -- Controles par calque --------------------------------------------------
    for layer_name, depth, knob_name in zip(layer_names, depths, knob_names):
        add_layer_controls(noop, layer_name, knob_name, depth,
                           min_depth, max_depth, face_cam_rot, vertical_rot)

    # -- Tab Setup Info (metadata pour update) ---------------------------------
    info_tab = nuke.Tab_Knob("setup_info_tab", "Setup Info")
    noop.addKnob(info_tab)

    update_script = (
        "import sys; sys.path.insert(0, r'r:/devMathieu/PS/dev');\n"
        "import main; main.update_psd(nuke.thisNode())")
    update_btn = nuke.PyScript_Knob("update_psd", "Update PSD", update_script)
    update_btn.setFlag(nuke.STARTLINE)
    noop.addKnob(update_btn)

    src_knob = nuke.String_Knob("source_name", "Source Node", source_name)
    noop.addKnob(src_knob)

    type_knob = nuke.String_Knob("source_type", "Source Type", source_type)
    noop.addKnob(type_knob)

    cam_knob = nuke.String_Knob("camera_name", "Camera Node", camera_name)
    noop.addKnob(cam_knob)

    fh_knob = nuke.String_Knob("frame_hold_name", "FrameHold", "")
    noop.addKnob(fh_knob)

    scene_knob = nuke.String_Knob("scene_name", "Scene", "")
    noop.addKnob(scene_knob)

    layers_knob = nuke.String_Knob("layer_list", "Layers", ";".join(knob_names))
    noop.addKnob(layers_knob)

    active_knob = nuke.String_Knob("active_layers", "Active Layers", "")
    noop.addKnob(active_knob)

    ignored_knob = nuke.String_Knob("ignored_list", "Ignored", "")
    noop.addKnob(ignored_knob)

    stamps_knob = nuke.Boolean_Knob("use_stamps_info", "Stamps")
    stamps_knob.setValue(use_stamps)
    noop.addKnob(stamps_knob)

    return noop, knob_names


def add_layer_controls(noop, layer_name, knob_name, depth,
                       min_depth, max_depth, face_cam_rot, vertical_rot):
    """
    Ajoute un slider depth + boutons rotation pour un layer dans le NoOp.
    Utilisable lors de la creation initiale et lors de l'update.
    """
    card_name = knob_name + "_card"

    slider = nuke.Double_Knob(knob_name, layer_name)
    slider.setRange(min_depth, max_depth)
    slider.setValue(depth)
    noop.addKnob(slider)

    v_script = "nuke.toNode('{}')['rotate'].setValue([0, {:.6f}, 0])".format(
        card_name, vertical_rot[1])
    v_btn = nuke.PyScript_Knob(knob_name + "_vert", "Vertical", v_script)
    noop.addKnob(v_btn)

    f_script = "nuke.toNode('{}')['rotate'].setValue([{:.6f}, {:.6f}, 0])".format(
        card_name, face_cam_rot[0], face_cam_rot[1])
    f_btn = nuke.PyScript_Knob(knob_name + "_face", "Face Cam", f_script)
    f_btn.clearFlag(nuke.STARTLINE)
    noop.addKnob(f_btn)


def _safe_knob_name(name):
    """Sanitize un nom de layer pour l'utiliser comme identifiant de knob Nuke."""
    safe = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    if not safe or safe[0].isdigit():
        safe = '_' + safe
    return safe
