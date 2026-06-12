"""
psd_splitter.py
Découpage d'un Read node PSD en une liste de Premult nodes (un par calque).
Crée des Shuffle2 (nouvelle génération) au lieu des anciens Shuffle.
"""

import nuke
from nukescripts import psd


def split_psd_node(psd_node):
    """
    Découpe un PSD Read node en calques individuels.
    Insere un OCIODisplay inverse (display -> scene_linear) si absent.
    Retourne une liste de Premult nodes, du calque le plus haut au plus bas.
    """
    backdrops_before = set(nuke.allNodes("BackdropNode"))
    dots_before      = set(nuke.allNodes("Dot"))
    psd.breakoutLayers(psd_node)

    # Collecter les Shuffles EN PREMIER (la traversée passe par les Dot nodes)
    raw_shuffles = _collect_shuffles(psd_node)

    # Supprimer backdrops et dots créés par breakoutLayers (on gère les nôtres)
    # Les Shuffles sont déjà collectés, on peut supprimer les Dots sans problème
    for bd in nuke.allNodes("BackdropNode"):
        if bd not in backdrops_before:
            nuke.delete(bd)
    for dot in nuke.allNodes("Dot"):
        if dot not in dots_before:
            nuke.delete(dot)

    # OCIODisplay inverse entre le PSD et les Shuffle2
    ocio_node = _ensure_ocio_display(psd_node)

    premult_nodes = []
    for raw_shuffle in raw_shuffles:
        # 1. Supprimer la chaîne Crop pendant qu'on est encore sur un Shuffle (classe attendue)
        _remove_crop_chain(raw_shuffle)
        # 2. Convertir vers Shuffle2 (ou no-op si déjà Shuffle2)
        shuffle2 = _to_shuffle2(raw_shuffle, ocio_node)
        # 3. Attacher le Premult
        premult = _attach_premult(shuffle2)
        premult_nodes.append(premult)

    return premult_nodes


def _collect_shuffles(node):
    """
    Parcourt récursivement les dépendants pour collecter tous les Shuffle/Shuffle2 nodes,
    en traversant les Dot nodes.
    """
    shuffles = []
    for dependent in node.dependent():
        if dependent.Class() in ("Shuffle", "Shuffle2"):
            shuffles.append(dependent)
        elif dependent.Class() == "Dot":
            shuffles.extend(_collect_shuffles(dependent))
    return shuffles


def _remove_crop_chain(shuffle_node):
    """
    Supprime les Crop nodes (et leur chaîne) créés par breakoutLayers().
    """
    for downstream in shuffle_node.dependent():
        if downstream.Class() == "Crop":
            _remove_to_leaf(downstream)


def _remove_to_leaf(node):
    """
    Descend jusqu'à la feuille du graphe puis remonte en supprimant les nodes,
    en s'arrêtant avant les Shuffle nodes.
    """
    children = node.dependent()
    if children:
        for child in children:
            _remove_to_leaf(child)
    else:
        _delete_upstream_until_shuffle(node)


def _delete_upstream_until_shuffle(node):
    """
    Supprime le node et remonte en supprimant les parents,
    jusqu'à atteindre un Shuffle ou Shuffle2 (qui est conservé).
    """
    for parent in node.dependencies():
        if parent.Class() in ("Shuffle", "Shuffle2"):
            nuke.delete(node)
            return
        _delete_upstream_until_shuffle(parent)
    nuke.delete(node)


def _to_shuffle2(node, psd_node):
    """
    Convertit un ancien Shuffle en Shuffle2.
    Si le node est déjà un Shuffle2, le retourne tel quel.
    """
    if node.Class() == "Shuffle2":
        return node

    # Récupérer le nom du calque PSD lu par l'ancien Shuffle
    layer_name = node["in"].value()

    # Récupérer les connexions aval avant suppression
    outputs = []
    for dep in list(node.dependent()):
        for i in range(dep.inputs()):
            if dep.input(i) is node:
                outputs.append((dep, i))

    x, y = node.xpos(), node.ypos()

    # Créer le Shuffle2 connecté directement au Read PSD
    shuffle2 = nuke.nodes.Shuffle2(inputs=[psd_node])
    shuffle2["in1"].setValue(layer_name)
    shuffle2["label"].setValue(layer_name)   # nom visible dans le DAG
    shuffle2.setXYpos(x, y)

    # Rewirer les connexions aval
    for dep, idx in outputs:
        dep.setInput(idx, shuffle2)

    nuke.delete(node)
    return shuffle2


def _attach_premult(shuffle2_node):
    """
    Crée un Premult node connecté sous le Shuffle2 node donné.
    Retourne le Premult node.
    """
    premult = nuke.nodes.Premult(inputs=[shuffle2_node])
    premult.setXYpos(shuffle2_node.xpos(), shuffle2_node.ypos() + 80)
    return premult


def _ensure_ocio_display(psd_node):
    """
    Verifie si un OCIODisplay inverse existe deja en sortie du PSD Read.
    Si oui, le retourne. Sinon, en cree un.

    Config : scene_linear -> sRGB Display, ACES 1.0 SDR Video, invert=True
    (convertit du display space vers scene_linear).
    """
    for dep in psd_node.dependent():
        if dep.Class() == "OCIODisplay" and dep["invert"].value():
            return dep

    ocio = nuke.nodes.OCIODisplay(inputs=[psd_node])
    ocio["colorspace"].setValue("scene_linear")
    ocio["display"].setValue("sRGB - Display")
    ocio["view"].setValue("ACES 1.0 - SDR Video")
    ocio["invert"].setValue(True)
    ocio.setXYpos(psd_node.xpos(), psd_node.ypos() + 80)

    return ocio
