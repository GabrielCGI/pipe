"""
main.py
Point d'entree du tool Layers to 3D Cards.

Supporte les Read nodes PSD et EXR multi-layer.

Usage depuis le Script Editor Nuke :
    import main
    main.run()
"""

import re

import nuke

from psd_splitter    import split_psd_node
from exr_splitter    import split_exr_node, _get_exr_layers
from depth_sampler   import (build_depth_pipeline, distribute_depths,
                             create_depth_controls, add_layer_controls,
                             install_depth_callback, execute_curve_tool,
                             FALLBACK_MIN_DEPTH, FALLBACK_MAX_DEPTH,
                             _safe_knob_name)
from card_builder    import build_card, get_card_rotations
from scene_assembler import (assemble_scene, create_layer_backdrop, layout_columns,
                             layout_depth_analysis, create_depth_section_backdrop,
                             layout_grouped_column,
                             BACKDROP_PADDING_X, COL_GAP, COL_BASE_WIDTH,
                             ROW_SHUFFLE, ROW_PREMULT, ROW_PROJECT, ROW_CARD)
from ui_dialog       import (show_selection_dialog, validate_inputs,
                             show_depth_range_dialog)


def run():
    """
    Lance le pipeline complet.
    Toute la creation de nodes est encapsulee dans un seul bloc undo.
    """
    selection = show_selection_dialog()
    if selection is None:
        return

    source_node      = selection["source_node"]
    source_type      = selection["source_type"]
    cg_node          = selection["cg_node"]
    camera_node      = selection["camera_node"]
    enable_grouping  = selection.get("enable_grouping", False)
    use_stamps       = selection.get("use_stamps", False)

    ok, error, depth_channel = validate_inputs(source_node, source_type, cg_node, camera_node)
    if not ok:
        nuke.message("Erreur : {}".format(error))
        return

    undo = nuke.Undo()
    undo.begin("Layers to 3D Cards")
    try:
        _process_layers(source_node, source_type, cg_node, camera_node,
                        enable_grouping, use_stamps, depth_channel)
    except Exception as e:
        undo.cancel()
        nuke.message("Erreur pendant le traitement :\n{}".format(str(e)))
        raise
    finally:
        undo.end()


def update_psd(noop):
    """
    Appele depuis le bouton Update PSD du NoOp globalControls.
    Detecte les layers ajoutes/supprimes et met a jour le setup 3D.
    """
    undo = nuke.Undo()
    undo.begin("Update PSD Layers")
    try:
        _update_psd_layers(noop)
    except Exception as e:
        undo.cancel()
        nuke.message("Erreur update :\n{}".format(str(e)))
        raise
    finally:
        undo.end()


def _update_psd_layers(noop):
    """
    Logique d'update :
      1. Liste les layers actuels de la source (lecture seule)
      2. Compare avec active_layers (whitelist individuelle) et ignored_list
      3. Affiche un dialog avec layers actifs, ignores, et nouveaux
      4. Nouveaux layers -> groupage optionnel + setup 3D
      5. Layers supprimes -> disable Card2
    """
    # -- Lire les metadonnees du NoOp ------------------------------------------
    source_name = noop["source_name"].value()
    source_type = noop["source_type"].value()
    camera_name = noop["camera_name"].value()
    fh_name = noop["frame_hold_name"].value()
    scene_name = noop["scene_name"].value()
    existing_list = noop["layer_list"].value().split(";")
    use_stamps = noop["use_stamps_info"].value()

    # Whitelist des layers individuels actifs
    active_val = noop["active_layers"].value() if noop.knob("active_layers") else ""
    active_set = set(active_val.split(";")) if active_val else set()

    ignored_val = noop["ignored_list"].value() if noop.knob("ignored_list") else ""
    ignored_set = set(ignored_val.split(";")) if ignored_val else set()

    source_node = nuke.toNode(source_name)
    camera_node = nuke.toNode(camera_name)
    frame_hold = nuke.toNode(fh_name)
    scene = nuke.toNode(scene_name)

    if not all([source_node, camera_node, frame_hold, scene]):
        nuke.message("Nodes introuvables. Verifiez le tab Setup Info.")
        return

    # -- Lister les layers actuels (lecture seule) -----------------------------
    current_layer_names = _get_source_layer_names(source_node, source_type)
    current_knob_names = [_safe_knob_name(n) for n in current_layer_names]

    known_set = active_set | ignored_set

    # Nouveaux layers = pas dans active ni ignored
    new_indices = [i for i, kn in enumerate(current_knob_names) if kn not in known_set]
    new_layer_names = [current_layer_names[i] for i in new_indices]

    # Layers supprimes = dans active_set mais plus dans la source
    removed_knobs = active_set - set(current_knob_names)

    if not new_layer_names and not removed_knobs:
        nuke.message("Aucun changement detecte dans les layers.")
        return

    # -- Disable les Card2 des layers supprimes --------------------------------
    for knob_name in existing_list:
        card = nuke.toNode("{}_card".format(knob_name))
        if card is None:
            continue
        if knob_name in active_set and knob_name in removed_knobs:
            card["disable"].setValue(True)

    # -- Dialog de selection pour les nouveaux layers --------------------------
    if not new_layer_names:
        msg = "{} layer(s) desactive(s)".format(len(removed_knobs))
        nuke.message("Update termine : {}".format(msg))
        return

    active_display = sorted(active_set - removed_knobs)
    ignored_display = sorted(ignored_set)

    from group_dialog import show_update_dialog
    result = show_update_dialog(new_layer_names, active_display, ignored_display)
    if result is None:
        return
    grouping, update_ignored_indices = result

    # Separer les ignores des nouveaux
    update_ignored_knobs = [_safe_knob_name(new_layer_names[i])
                            for i in update_ignored_indices]

    # Mettre a jour la liste des ignores
    new_ignored = ignored_set | set(update_ignored_knobs)
    noop["ignored_list"].setValue(";".join(sorted(new_ignored)))

    # Filtrer les layers ignores du grouping
    ignored_idx_set = set(update_ignored_indices)
    grouping = [(name, [i for i in indices if i not in ignored_idx_set])
                for name, indices in grouping]
    grouping = [(name, indices) for name, indices in grouping if indices]

    if not grouping:
        msg = []
        if removed_knobs:
            msg.append("{} layer(s) desactive(s)".format(len(removed_knobs)))
        if update_ignored_knobs:
            msg.append("{} layer(s) ignore(s)".format(len(update_ignored_knobs)))
        nuke.message("Update termine : {}".format(", ".join(msg)))
        return

    # -- Creer le setup 3D pour les nouveaux layers ----------------------------
    face_cam_rot, vertical_rot = get_card_rotations(camera_node)
    min_depth = FALLBACK_MIN_DEPTH
    max_depth = FALLBACK_MAX_DEPTH

    existing_depths = []
    for kn in existing_list:
        if noop.knob(kn):
            existing_depths.append(noop[kn].getValue())
    if existing_depths:
        min_depth = min(existing_depths)
        max_depth = max(existing_depths)

    next_scene_input = 0
    while scene.input(next_scene_input) is not None:
        next_scene_input += 1

    if source_type == "psd":
        input_node = _find_ocio_display(source_node)
        if input_node is None:
            input_node = source_node
    else:
        input_node = source_node

    src_anchor = None
    if use_stamps:
        import stamps
        src_title = "PSD" if source_type == "psd" else "EXR"
        src_anchor = _get_or_create_anchor(source_node, src_title)

    col_x = _find_rightmost_backdrop_edge()
    _switch_to_depth_tab(noop)

    added_knob_names = []
    added_active_knobs = []
    used_names = set(existing_list)

    for group_name, indices in grouping:
        premult_nodes_grp = []
        shuffle_nodes_grp = []
        for i in indices:
            layer_name = new_layer_names[i]
            shuffle2, premult = _create_layer_setup(layer_name, input_node)
            if use_stamps and src_anchor is not None:
                wired = _create_wired(stamps, src_anchor)
                shuffle2.setInput(0, wired)
                wired.setXYpos(col_x, ROW_SHUFFLE - 100)
            premult_nodes_grp.append(premult)
            shuffle_nodes_grp.append(shuffle2)
            added_active_knobs.append(_safe_knob_name(layer_name))

        # Grouper si multi-layer
        if len(premult_nodes_grp) > 1:
            merged, detail = _merge_layer_group(premult_nodes_grp)
            final_premult = merged
            knob_name = _unique_knob_name(group_name, used_names)
        else:
            final_premult = premult_nodes_grp[0]
            knob_name = _unique_knob_name(new_layer_names[indices[0]], used_names)
            detail = None
        used_names.add(knob_name)

        depth = (min_depth + max_depth) / 2.0

        add_layer_controls(noop, group_name, knob_name, depth,
                           min_depth, max_depth, face_cam_rot, vertical_rot)

        # Positionner
        if detail is not None:
            layout_grouped_column(col_x, detail, None, None)
        else:
            shuffle_nodes_grp[0].setXYpos(col_x, ROW_SHUFFLE)
            premult_nodes_grp[0].setXYpos(col_x, ROW_PREMULT)

        # FrameHold Dot
        fh_dot = nuke.nodes.Dot(inputs=[frame_hold])
        fh_dot["hide_input"].setValue(True)
        fh_dot["label"].setValue("\n[value input.name]")
        fh_dot["note_font"].setValue("Verdana Bold")
        fh_dot["note_font_size"].setValue(20)
        fh_dot.setXYpos(col_x - 120, ROW_PROJECT)

        card = build_card(camera_node, final_premult, noop, knob_name,
                          knob_name, proj_camera=fh_dot)
        project3d = card.input(0)
        if project3d is not None:
            project3d.setXYpos(col_x, ROW_PROJECT)
        card.setXYpos(col_x, ROW_CARD)

        scene.setInput(next_scene_input, card)
        next_scene_input += 1

        all_nodes = shuffle_nodes_grp + premult_nodes_grp
        if project3d is not None:
            all_nodes.append(project3d)
        all_nodes.append(card)
        create_layer_backdrop([n for n in all_nodes if n is not None], group_name)

        added_knob_names.append(knob_name)
        col_x += COL_BASE_WIDTH + BACKDROP_PADDING_X * 2 + COL_GAP

    # -- Mettre a jour les metadonnees -----------------------------------------
    updated_list = existing_list + added_knob_names
    noop["layer_list"].setValue(";".join(updated_list))

    new_active = active_set | set(added_active_knobs)
    noop["active_layers"].setValue(";".join(sorted(new_active)))

    msg = []
    if added_knob_names:
        msg.append("{} card(s) ajoutee(s)".format(len(added_knob_names)))
    if removed_knobs:
        msg.append("{} layer(s) desactive(s)".format(len(removed_knobs)))
    if update_ignored_knobs:
        msg.append("{} layer(s) ignore(s)".format(len(update_ignored_knobs)))
    nuke.message("Update termine : {}".format(", ".join(msg)))


def _unique_knob_name(base_name, existing_names):
    """
    Genere un knob_name unique a partir de base_name.
    Si le nom sanitise existe deja dans existing_names, ajoute _01, _02, etc.
    """
    knob = _safe_knob_name(base_name)
    if knob not in existing_names:
        return knob
    for i in range(1, 100):
        candidate = "{}_{:02d}".format(knob, i)
        if candidate not in existing_names:
            return candidate
    return knob


def _find_rightmost_backdrop_edge():
    """Retourne la position X a droite du dernier BackdropNode existant + marge."""
    max_right = 0
    for bd in nuke.allNodes("BackdropNode"):
        right = bd.xpos() + bd["bdwidth"].value()
        if right > max_right:
            max_right = right
    return int(max_right + COL_GAP + BACKDROP_PADDING_X)


def _switch_to_depth_tab(noop):
    """
    Ajoute un Tab_Knob 'depth_tab' pour forcer les prochains addKnob
    a s'inserer dans le tab Depth Control (pas dans Setup Info).
    """
    tab = nuke.Tab_Knob("depth_tab", "Depth Control")
    noop.addKnob(tab)


def _get_source_layer_names(source_node, source_type):
    """
    Liste les noms de layers d'un Read node (PSD ou EXR) en lisant ses channels.
    Aucun node n'est cree — lecture seule.
    """
    if source_type == "exr":
        return _get_exr_layers(source_node)

    # PSD : layers = channels hors rgba/alpha
    psd_exclude = {"rgba", "alpha"}
    channels = source_node.channels()
    seen = set()
    layers = []
    for ch in channels:
        layer = ch.split(".")[0]
        if layer.lower() not in psd_exclude and layer not in seen:
            seen.add(layer)
            layers.append(layer)
    return layers


def _find_ocio_display(source_node):
    """Cherche l'OCIODisplay inverse existant parmi les dependants du Read PSD."""
    for dep in source_node.dependent():
        if dep.Class() == "OCIODisplay" and dep["invert"].value():
            return dep
    return None


def _create_layer_setup(layer_name, input_node):
    """Cree Shuffle2 + Premult pour un layer, connecte a input_node."""
    shuffle2 = nuke.nodes.Shuffle2(inputs=[input_node])
    shuffle2["in1"].setValue(layer_name)
    shuffle2["label"].setValue(layer_name)
    premult = nuke.nodes.Premult(inputs=[shuffle2])
    return shuffle2, premult


def _process_layers(source_node, source_type, cg_node, camera_node,
                    enable_grouping=False, use_stamps=False,
                    depth_channel="depth_extra.z"):
    """
    Pipeline principal :
      1. Decoupe la source (PSD ou EXR) en Premult nodes (avec Shuffle2)
      2. (Optionnel) Groupage interactif des layers
      3. Analyse la plage de profondeur via depth_extra.z + CurveTool
      4. Distribue les calques entre min et max depth
      5. Pour chaque calque/groupe : cree un NoOp controleur + Project3D + Card2
      6. Organise le DAG (colonnes + backdrops)
      7. Assemble la scene 3D (Scene + ScanlineRender)
    """
    if source_type == "psd":
        premult_nodes = split_psd_node(source_node)
    else:
        premult_nodes = split_exr_node(source_node)

    if not premult_nodes:
        nuke.message("Aucun calque trouve dans la source.")
        return

    # -- Noms des calques ------------------------------------------------------
    layer_names = []
    for premult in premult_nodes:
        shuffle2 = premult.input(0)
        layer_names.append(shuffle2["label"].value() if shuffle2 else "calque")

    # Whitelist des layers individuels (avant groupage, pour l'update)
    active_individual_knobs = [_safe_knob_name(n) for n in layer_names]

    # -- Dialog de groupage / exclusion (toujours affiche) ---------------------
    group_details = None
    from group_dialog import show_group_dialog
    result = show_group_dialog(layer_names, enable_grouping=enable_grouping)
    if result is None:
        return  # Utilisateur a annule
    grouping, ignored_indices = result

    # Filtrer les layers ignores (pas de setup 3D cree pour eux)
    ignored_knob_names = []
    if ignored_indices:
        ignored_set = set(ignored_indices)
        total = len(premult_nodes)
        # Memoriser les knob_names ignores pour le NoOp
        ignored_knob_names = [_safe_knob_name(layer_names[i]) for i in ignored_indices]
        # Supprimer les Shuffle2 et Premult des layers ignores du DAG
        for i in ignored_indices:
            premult = premult_nodes[i]
            shuffle2 = premult.input(0)
            nuke.delete(premult)
            if shuffle2 is not None:
                nuke.delete(shuffle2)
        premult_nodes = [p for i, p in enumerate(premult_nodes) if i not in ignored_set]
        layer_names = [n for i, n in enumerate(layer_names) if i not in ignored_set]
        # Re-mapper les indices du grouping (old_idx -> new_idx sans les ignored)
        kept = [i for i in range(total) if i not in ignored_set]
        old_to_new = {old: new for new, old in enumerate(kept)}
        grouping = [(name, [old_to_new[i] for i in indices])
                    for name, indices in grouping]

    if enable_grouping and grouping:
        premult_nodes, layer_names, group_details = _apply_grouping(
            premult_nodes, layer_names, grouping)

    # -- Stamps optionnels (Anchors sur les 3 entrees) --------------------------
    src_anchor = None
    if use_stamps:
        import stamps
        src_title = "PSD" if source_type == "psd" else "EXR"
        src_anchor = _get_or_create_anchor(source_node, src_title)
        if cg_node is not None:
            cg_anchor = _get_or_create_anchor(cg_node, "CG")
        cam_anchor = _get_or_create_anchor(camera_node, "CAM",
                                           node_type="Camera")

        # Reconnecte chaque Shuffle2 a un Wired PSD
        # Collecte d'abord tous les Shuffle2 (solo et groupes)
        all_shuffles = []
        if group_details:
            for i, detail in enumerate(group_details):
                if detail is not None:
                    all_shuffles.extend(detail["shuffles"])
                else:
                    shuf = premult_nodes[i].input(0)
                    if shuf is not None:
                        all_shuffles.append(shuf)
        else:
            for premult in premult_nodes:
                shuf = premult.input(0)
                if shuf is not None:
                    all_shuffles.append(shuf)

        # L'Anchor PSD doit etre sur le node qui alimente les Shuffles
        # (OCIODisplay pour PSD, Read pour EXR), pas sur le Read brut
        if all_shuffles:
            shuffle_source = all_shuffles[0].input(0)
            if shuffle_source is not None and shuffle_source != source_node:
                # OCIODisplay ou autre node intermediaire
                src_anchor.setInput(0, shuffle_source)
                src_anchor.setXYpos(shuffle_source.xpos(),
                                    shuffle_source.ypos() + 150)

        for shuffle2 in all_shuffles:
            wired = _create_wired(stamps, src_anchor)
            shuffle2.setInput(0, wired)

        # Wired CG pour le depth pipeline (seulement si CG present)
        if cg_node is not None:
            cg_input = _create_wired(stamps, cg_anchor)
        else:
            cg_input = None
        cam_input = cam_anchor
    else:
        cg_input = cg_node
        cam_input = camera_node

    # -- Profondeur : analyse auto (CurveTool) ou saisie manuelle --------------
    depth_nodes = None
    p2p_node = None
    if depth_channel and cg_input is not None:
        depth_nodes = build_depth_pipeline(cg_input, depth_channel)
        p2p_node = _create_position_to_points(cg_input)
        min_depth = FALLBACK_MIN_DEPTH
        max_depth = FALLBACK_MAX_DEPTH
    else:
        depth_range = show_depth_range_dialog()
        if depth_range is None:
            return
        min_depth, max_depth = depth_range

    depths = distribute_depths(len(premult_nodes), min_depth, max_depth)

    # -- Rotations camera (pour les boutons Vertical / Face Cam) ---------------
    face_cam_rot, vertical_rot = get_card_rotations(camera_node)

    # -- NoOp global avec un slider par calque ---------------------------------
    depth_ctrl, knob_names = create_depth_controls(
        layer_names, depths, min_depth, max_depth,
        face_cam_rot, vertical_rot,
        source_name=source_node.name(), source_type=source_type,
        camera_name=camera_node.name(), use_stamps=use_stamps)
    depth_ctrl.setXYpos(-300, 0)

    # Stocker les layers ignores et la whitelist individuelle dans le NoOp
    if ignored_knob_names:
        depth_ctrl["ignored_list"].setValue(";".join(ignored_knob_names))
    # Whitelist = layers individuels actifs (avant groupage), sans les ignores
    active_knobs_filtered = [k for k in active_individual_knobs
                             if k not in set(ignored_knob_names)]
    depth_ctrl["active_layers"].setValue(";".join(active_knobs_filtered))

    # -- Callback : le CurveTool mettra a jour le NoOp apres execution ---------
    if depth_nodes is not None:
        install_depth_callback(depth_nodes["curve_tool"],
                               depth_ctrl.name(), knob_names)

    # -- FrameHold partage par tous les Project3D ------------------------------
    frame_hold = nuke.nodes.FrameHold(inputs=[cam_input])
    frame_hold["firstFrame"].setValue(_get_projection_frame(source_node))
    frame_hold.setXYpos(camera_node.xpos(), camera_node.ypos() + 100)

    layer_groups = []
    card_nodes   = []

    for col_idx, (premult, knob_name, _) in enumerate(
            zip(premult_nodes, knob_names, layer_names)):
        shuffle2 = premult.input(0)

        # Dot hide_input pour connecter le FrameHold au Project3D
        fh_dot = nuke.nodes.Dot(inputs=[frame_hold])
        fh_dot["hide_input"].setValue(True)
        fh_dot["label"].setValue("\n[value input.name]")
        fh_dot["note_font"].setValue("Verdana Bold")
        fh_dot["note_font_size"].setValue(20)

        # Card avec expressions linkees au NoOp global
        card      = build_card(camera_node, premult, depth_ctrl, knob_name,
                               knob_name, proj_camera=fh_dot)
        project3d = card.input(0)

        card_nodes.append(card)

        detail = group_details[col_idx] if group_details else None
        layer_groups.append({
            "shuffle2":     shuffle2,
            "premult":      premult,
            "project3d":    project3d,
            "card":         card,
            "fh_dot":       fh_dot,
            "group_detail": detail,
        })

    # -- Layout et backdrops ---------------------------------------------------
    col_positions = layout_columns(layer_groups)
    if depth_nodes is not None:
        layout_depth_analysis(depth_nodes, p2p_node=p2p_node)
        create_depth_section_backdrop(depth_nodes)

    # -- Positionnement des Wired stamps (apres layout des Shuffles) -----------
    if use_stamps and src_anchor is not None:
        for group in layer_groups:
            detail = group.get("group_detail")
            if detail is not None:
                # Groupe : un Wired par Shuffle
                for shuf in detail["shuffles"]:
                    if shuf is not None:
                        wired = shuf.input(0)
                        if wired is not None:
                            wired.setXYpos(shuf.xpos(), shuf.ypos() - 80)
            else:
                # Solo : un Wired pour le Shuffle
                shuf = group["shuffle2"]
                if shuf is not None:
                    wired = shuf.input(0)
                    if wired is not None:
                        wired.setXYpos(shuf.xpos(), shuf.ypos() - 80)

    for col_idx, group in enumerate(layer_groups):
        detail = group.get("group_detail")
        if detail is not None:
            # Groupe : le backdrop englobe tous les nodes internes
            all_nodes = (detail["shuffles"] + detail["premults"]
                         + detail["merges"] + detail["dots"]
                         + [group["project3d"], group["card"]])
            all_nodes = [n for n in all_nodes if n is not None]
            create_layer_backdrop(all_nodes, layer_names[col_idx])
        else:
            # Layer solo
            shuffle2 = group["shuffle2"]
            name = shuffle2["label"].value() if shuffle2 else "calque"
            nodes = [group[k] for k in ("shuffle2", "premult", "project3d", "card")]
            create_layer_backdrop(nodes, name)

    center_x = (col_positions[0] + col_positions[-1]) // 2
    _, scene = assemble_scene(card_nodes, camera_node, center_x,
                              p2p_node=p2p_node)

    # Stocker les refs dans le NoOp pour l'update
    depth_ctrl["frame_hold_name"].setValue(frame_hold.name())
    depth_ctrl["scene_name"].setValue(scene.name())

    # -- Breakdown PSD natif (reference, non connecte au setup 3D) -------------
    if source_type == "psd":
        _create_psd_breakdown(source_node, col_positions,
                              src_anchor=src_anchor, use_stamps=use_stamps)

    # -- Execution differee du CurveTool (le graph est complet) ----------------
    # Le callback afterRender injecte les vraies profondeurs dans le NoOp,
    # ce qui met a jour automatiquement les positions des cards via expressions.
    if depth_nodes is not None:
        execute_curve_tool(depth_nodes["curve_tool"])


def _apply_grouping(premult_nodes, layer_names, grouping):
    """
    Applique le resultat du dialog de groupage.

    grouping : list[tuple[str, list[int]]]
      ex: [("Sky", [0, 1]), ("sun", [2]), ("Group 2", [3, 4, 5])]

    Pour les groupes multi-layer, les Premult nodes sont chaines
    via Merge2 (over). Le resultat remplace les nodes individuels.

    Retourne : (new_premult_nodes, new_layer_names, group_details)
      group_details[i] = None pour un layer solo,
                         dict pour un groupe (shuffles, premults, merges, dots)
    """
    new_premult_nodes = []
    new_layer_names = []
    group_details = []

    for group_name, indices in grouping:
        if len(indices) == 1:
            new_premult_nodes.append(premult_nodes[indices[0]])
            new_layer_names.append(layer_names[indices[0]])
            group_details.append(None)
        else:
            nodes_to_merge = [premult_nodes[i] for i in indices]
            merged, detail = _merge_layer_group(nodes_to_merge)
            new_premult_nodes.append(merged)
            new_layer_names.append(group_name)
            group_details.append(detail)

    return new_premult_nodes, new_layer_names, group_details


def _merge_layer_group(premult_nodes_to_merge):
    """
    Chaine N Premult nodes via Merge2 (operation: over) avec Dots de routage.
    Index 0 = fond (B input), les suivants sont merges par-dessus (A input).

    Retourne (last_merge, detail_dict) avec :
      detail_dict = {
          "shuffles": [shuffle2_0, ...],
          "premults": [premult_0, ...],
          "merges":   [merge_1, ...],
          "dots":     [dot_1, ...],
      }
    """
    shuffles = [p.input(0) for p in premult_nodes_to_merge]
    merges = []
    dots = []

    result = premult_nodes_to_merge[0]
    for i in range(1, len(premult_nodes_to_merge)):
        dot = nuke.nodes.Dot(inputs=[premult_nodes_to_merge[i]])
        dots.append(dot)
        merge = nuke.nodes.Merge2(inputs=[result, dot])
        merge["operation"].setValue("over")
        merges.append(merge)
        result = merge

    detail = {
        "shuffles": shuffles,
        "premults": list(premult_nodes_to_merge),
        "merges":   merges,
        "dots":     dots,
    }
    return result, detail


def _create_wired(stamps_module, anchor_node):
    """
    Cree un Wired stamp connecte a un Anchor, avec gestion propre
    de la selection Nuke (le module Stamps utilise la selection interne).
    """
    # Deselectionner tout
    for n in nuke.allNodes():
        n.setSelected(False)

    wired = stamps_module.wired(anchor=anchor_node)

    # Deselectionner le wired cree pour eviter que le prochain
    # appel ne se chaine dessus au lieu de l'anchor
    if wired is not None:
        wired.setSelected(False)
    return wired


def _get_projection_frame(source_node):
    """
    Extrait le numero de frame depuis le nom de fichier du Read node source.
    Ex: "SQ040-SH0200_PAINTOVER_OUT_v006.1049.psd" -> 1049
    Fallback sur la frame courante si aucun numero trouve.
    """
    file_path = source_node["file"].value()
    match = re.search(r'\.(\d+)\.\w+$', file_path)
    if match:
        return int(match.group(1))
    return int(nuke.frame())


def _create_psd_breakdown(source_node, col_positions,
                          src_anchor=None, use_stamps=False):
    """
    Cree le breakdown PSD natif (via breakoutLayers) comme reference visuelle.
    Positionne au-dessus du setup 3D pour ne pas chevaucher les colonnes.
    Si use_stamps, reconnecte les Shuffles du breakdown a un Wired PSD.
    """
    from nukescripts import psd

    # Collecter les nodes existants pour isoler ceux crees par breakoutLayers
    nodes_before = set(nuke.allNodes())

    psd.breakoutLayers(source_node)

    # Identifier les nouveaux nodes
    new_nodes = [n for n in nuke.allNodes() if n not in nodes_before]
    if not new_nodes:
        return

    # Inserer un Wired PSD entre le Read et le premier Dot de la chaine
    if use_stamps and src_anchor is not None:
        import stamps
        new_nodes_set = set(new_nodes)
        first_dot = None
        for node in new_nodes:
            if node.Class() == "Dot":
                inp = node.input(0)
                if inp is not None and inp not in new_nodes_set:
                    first_dot = node
                    break
        if first_dot is not None:
            wired = _create_wired(stamps, src_anchor)
            first_dot.setInput(0, wired)
            new_nodes.append(wired)

    # Positionner le breakdown au-dessus du setup 3D (y negatif)
    # pour ne pas etre chevauche par les colonnes de cards
    from scene_assembler import ROW_SHUFFLE, BACKDROP_PADDING_Y

    min_x = min(n.xpos() for n in new_nodes)
    min_y = min(n.ypos() for n in new_nodes)
    max_y = max(n.ypos() + n.screenHeight() for n in new_nodes)
    breakdown_height = max_y - min_y

    offset_x = col_positions[0] - min_x
    offset_y = (ROW_SHUFFLE - BACKDROP_PADDING_Y - breakdown_height - 200) - min_y

    for node in new_nodes:
        node.setXYpos(node.xpos() + offset_x, node.ypos() + offset_y)


def _create_position_to_points(cg_input):
    """
    Cree un Dot + PositionToPoints2 connecte a la sortie CG
    pour visualiser le nuage de points 3D dans la scene.
    """
    nuke.tcl("add_layer {P P.x P.y P.z}")
    nuke.tcl("add_layer {N N.x N.y N.z}")

    dot = nuke.nodes.Dot(inputs=[cg_input])
    p2p = nuke.nodes.PositionToPoints2(inputs=[dot])
    p2p["render_mode"].setValue("off")
    p2p["cast_shadow"].setValue(False)
    p2p["receive_shadow"].setValue(False)
    p2p["P_channel"].setValue("P")
    p2p["N_channel"].setValue("N")
    p2p["detail"].setValue(0.7)
    p2p["pointSize"].setValue(2)
    return p2p


def _get_or_create_anchor(node, title, node_type="2D"):
    """
    Cherche un Anchor Stamps existant connecte a node avec ce titre.
    Si aucun n'existe, en cree un nouveau.
    """
    import stamps
    existing = stamps.findAnchorsByTitle(title)
    for a in existing:
        if a.input(0) == node:
            return a
    # Deselectionner tout avant stamps.anchor() — le module Stamps utilise
    # la selection Nuke et peut reconnecter des nodes selectionnes a l'anchor
    for n in nuke.allNodes():
        n.setSelected(False)
    anchor = stamps.anchor(title=title, node_type=node_type)
    anchor.setInput(0, node)
    anchor.setXYpos(node.xpos(), node.ypos() + 150)
    return anchor
