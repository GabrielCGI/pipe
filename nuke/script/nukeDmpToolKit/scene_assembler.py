"""
scene_assembler.py
Assemblage de la scene 3D Nuke et organisation du DAG.

Layout par colonne (une par calque PSD) :
  Row 0  :  Shuffle2
  Row 1  :  Premult
  Row 2  :  Project3D
  Row 3  :  Card2
  -----
  Row 4  :  Scene  |  ScanlineRender

Section depth analysis (colonne a gauche) :
  EdgeExtend -> Copy -> Expression (1/z) -> CurveTool
"""

import nuke

# -- Positions des lignes (y) -- section cards ---------------------------------
ROW_SHUFFLE  =    0
ROW_PREMULT  =  160
ROW_PROJECT  =  800
ROW_CARD     = 1000
ROW_SCENE    = 1600
ROW_SCANLINE = 1700

# -- Section depth analysis (colonne unique a gauche) --------------------------
DEPTH_COL_X       = -1000
ROW_DEPTH_EXTEND  =    0
ROW_DEPTH_COPY    =  150
ROW_DEPTH_EXPR    =  300
ROW_DEPTH_CROP    =  450
ROW_DEPTH_CURVE   =  600
ROW_DEPTH_P2P     =  800

# -- Espacement horizontal entre colonnes --------------------------------------
COL_BASE_WIDTH = 300   # largeur de base d'une colonne solo (un seul node)
COL_GAP        = 200   # ecart minimum entre les bords des backdrops

# -- Padding backdrops (espace autour des nodes) -------------------------------
BACKDROP_PADDING_X = 400
BACKDROP_PADDING_Y = 400
# Padding compact pour la section depth analysis
BACKDROP_PADDING_SMALL = 55

# -- Layout groupes (Shuffle espaces, merge chain verticale) -------------------
GROUP_SHUFFLE_SPACING = 110
GROUP_PREMULT_OFFSET  = 78
GROUP_MERGE_START     = 120
GROUP_MERGE_SPACING   = 144
DOT_OFFSET_X          = 34
DOT_OFFSET_Y          = 3


def assemble_scene(card_nodes, camera_node, center_x, p2p_node=None):
    """
    Connecte tous les cards dans une Scene, puis dans un ScanlineRender.
    Positionne Scene et ScanlineRender sous le centre du DAG.

    Retourne le ScanlineRender node.
    """
    scene = nuke.nodes.Scene()
    for i, card in enumerate(card_nodes):
        scene.setInput(i, card)
    if p2p_node is not None:
        scene.setInput(len(card_nodes), p2p_node)

    scanline = nuke.nodes.ScanlineRender()
    scanline.setInput(1, scene)
    scanline.setInput(2, camera_node)

    scene.setXYpos(center_x, ROW_SCENE)
    scanline.setXYpos(center_x, ROW_SCANLINE)

    return scanline, scene


def create_layer_backdrop(nodes, label):
    """
    Cree un BackdropNode englobant les nodes donnes (une colonne de calque).
    Grande taille pour laisser de l'espace de travail aux artistes.
    """
    valid_nodes = [n for n in nodes if n is not None]
    if not valid_nodes:
        return None
    return _create_backdrop(valid_nodes, "<center>{}".format(label),
                            font_size=50, font_name="Verdana Bold",
                            padding_x=BACKDROP_PADDING_X,
                            padding_y=BACKDROP_PADDING_Y)


def _column_content_width(group):
    """Calcule la largeur du contenu d'une colonne (sans padding backdrop)."""
    detail = group.get("group_detail")
    if detail is not None:
        num_shuffles = len(detail["shuffles"])
        return max((num_shuffles - 1) * GROUP_SHUFFLE_SPACING, 0)
    return COL_BASE_WIDTH


def layout_columns(layer_groups):
    """
    Positionne les nodes en colonnes lisibles dans le DAG.
    Les positions X sont dynamiques pour eviter le chevauchement des backdrops.

    layer_groups : liste de dicts avec les cles :
        "shuffle2", "premult", "project3d", "card"

    Retourne la liste des positions X calculees.
    """
    row_map = {
        "shuffle2":  ROW_SHUFFLE,
        "premult":   ROW_PREMULT,
        "project3d": ROW_PROJECT,
        "card":      ROW_CARD,
    }

    # -- Calcul dynamique des positions X --------------------------------------
    col_widths = [_column_content_width(g) for g in layer_groups]
    col_positions = []
    for col_idx in range(len(layer_groups)):
        if col_idx == 0:
            col_x = 0
        else:
            prev_right = col_positions[col_idx - 1] + col_widths[col_idx - 1] + BACKDROP_PADDING_X
            col_x = prev_right + COL_GAP + BACKDROP_PADDING_X
        col_positions.append(col_x)

    # -- Positionnement des nodes ----------------------------------------------
    for col_idx, group in enumerate(layer_groups):
        x = col_positions[col_idx]
        detail = group.get("group_detail")
        if detail is not None:
            layout_grouped_column(x, detail,
                                  group.get("project3d"),
                                  group.get("card"))
        else:
            for key, row_y in row_map.items():
                node = group.get(key)
                if node is not None:
                    node.setXYpos(x, row_y)

        # FrameHold Dot : a gauche du Project3D
        fh_dot = group.get("fh_dot")
        if fh_dot is not None:
            fh_dot.setXYpos(x - 120, ROW_PROJECT)

    return col_positions


def layout_grouped_column(col_x, group_detail, project3d, card):
    """
    Positionne les nodes d'un groupe multi-layer :
      - Shuffles espaces horizontalement (110px)
      - Premults sous chaque Shuffle (78px)
      - Merge chain verticale alignee sur le 1er Shuffle
      - Dots de routage (angle droit Premult -> Merge)
      - Project3D et Card2 en dessous
    """
    shuffles = group_detail["shuffles"]
    premults = group_detail["premults"]
    merges   = group_detail["merges"]
    dots     = group_detail["dots"]

    # -- Shuffles et Premults --------------------------------------------------
    for i, (shuf, prem) in enumerate(zip(shuffles, premults)):
        sx = col_x + i * GROUP_SHUFFLE_SPACING
        if shuf is not None:
            shuf.setXYpos(sx, ROW_SHUFFLE)
        prem.setXYpos(sx, ROW_SHUFFLE + GROUP_PREMULT_OFFSET)

    # -- Merge chain (alignee sur col_x = 1er Shuffle) ------------------------
    premult_bottom = ROW_SHUFFLE + GROUP_PREMULT_OFFSET + 30  # ~screenHeight
    merge_start_y = premult_bottom + GROUP_MERGE_START

    for i, merge in enumerate(merges):
        merge.setXYpos(col_x, merge_start_y + i * GROUP_MERGE_SPACING)

    # -- Dots de routage (1 par Merge, relie au Premult i+1) -------------------
    for i, dot in enumerate(dots):
        premult_x = col_x + (i + 1) * GROUP_SHUFFLE_SPACING
        merge_y = merge_start_y + i * GROUP_MERGE_SPACING
        dot.setXYpos(premult_x + DOT_OFFSET_X, merge_y + DOT_OFFSET_Y)

    # -- Project3D et Card2 ----------------------------------------------------
    if project3d is not None:
        project3d.setXYpos(col_x, ROW_PROJECT)
    if card is not None:
        card.setXYpos(col_x, ROW_CARD)


def layout_depth_analysis(depth_nodes, p2p_node=None):
    """
    Positionne les nodes d'analyse de profondeur en colonne a gauche du DAG.

    depth_nodes : dict avec "edge_extend", "copy", "expr_inv", "crop", "curve_tool"
    p2p_node    : PositionToPoints2 optionnel (positionne sous le CurveTool)
    """
    row_map = {
        "edge_extend": ROW_DEPTH_EXTEND,
        "copy":        ROW_DEPTH_COPY,
        "expr_inv":    ROW_DEPTH_EXPR,
        "crop":        ROW_DEPTH_CROP,
        "curve_tool":  ROW_DEPTH_CURVE,
    }
    for key, row_y in row_map.items():
        node = depth_nodes.get(key)
        if node is not None:
            node.setXYpos(DEPTH_COL_X, row_y)

    if p2p_node is not None:
        # Dot d'entree du P2P juste au-dessus
        dot_input = p2p_node.input(0)
        if dot_input is not None:
            dot_input.setXYpos(DEPTH_COL_X + 200, ROW_DEPTH_P2P - 80)
        p2p_node.setXYpos(DEPTH_COL_X + 200, ROW_DEPTH_P2P)

    # Positionne l'input du EdgeExtend (Wired CG ou Read CG) au-dessus
    edge_ext = depth_nodes.get("edge_extend")
    if edge_ext is not None:
        cg_input = edge_ext.input(0)
        if cg_input is not None:
            cg_input.setXYpos(DEPTH_COL_X, ROW_DEPTH_EXTEND - 80)


def create_depth_section_backdrop(depth_nodes):
    """
    Cree un BackdropNode englobant la section d'analyse de profondeur.
    """
    valid = [n for n in depth_nodes.values() if n is not None]
    if not valid:
        return None
    return _create_backdrop(valid, "DEPTH ANALYSIS",
                            font_size=20, color=0x2244AAFF,
                            extra_top=30,
                            padding_x=BACKDROP_PADDING_SMALL,
                            padding_y=BACKDROP_PADDING_SMALL)


def _create_backdrop(nodes, label, font_size=16, color=None, extra_top=0,
                     font_name=None, padding_x=BACKDROP_PADDING_SMALL,
                     padding_y=BACKDROP_PADDING_SMALL):
    """
    Cree un BackdropNode englobant les nodes donnes.
    """
    min_x, min_y, max_x, max_y = _get_nodes_bbox(nodes)

    backdrop = nuke.nodes.BackdropNode()
    backdrop["xpos"].setValue(min_x - padding_x)
    backdrop["ypos"].setValue(min_y - padding_y - extra_top)
    backdrop["bdwidth"].setValue((max_x - min_x) + padding_x * 2)
    backdrop["bdheight"].setValue((max_y - min_y) + padding_y * 2 + extra_top)
    backdrop["label"].setValue(label)
    backdrop["note_font_size"].setValue(font_size)
    if font_name is not None:
        backdrop["note_font"].setValue(font_name)
    if color is not None:
        backdrop["tile_color"].setValue(color)
    return backdrop


def _get_nodes_bbox(nodes):
    """
    Retourne (min_x, min_y, max_x, max_y) englobant tous les nodes.
    """
    min_x = min(n.xpos() for n in nodes)
    min_y = min(n.ypos() for n in nodes)
    max_x = max(n.xpos() + n.screenWidth()  for n in nodes)
    max_y = max(n.ypos() + n.screenHeight() for n in nodes)
    return min_x, min_y, max_x, max_y
