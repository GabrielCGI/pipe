"""
exr_splitter.py
Decoupage d'un Read node EXR multi-layer en une liste de Premult nodes
(un par layer).

Contrairement au PSD, pas besoin de breakoutLayers ni d'OCIODisplay inverse :
les layers EXR sont deja accessibles comme channels Nuke et typiquement
en scene_linear.
"""

import nuke

# Layers techniques a exclure du split (pas des calques visuels)
EXCLUDE_LAYERS = {
    "rgba", "rgb", "alpha", "depth", "depth_extra",
    "forward", "backward", "motion", "crypto00", "crypto01", "crypto02",
}


def split_exr_node(exr_node):
    """
    Decoupe un EXR Read node multi-layer en calques individuels.
    Retourne une liste de Premult nodes, un par layer.
    """
    layers = _get_exr_layers(exr_node)

    if not layers:
        return []

    premult_nodes = []
    for layer_name in layers:
        shuffle2 = nuke.nodes.Shuffle2(inputs=[exr_node])
        shuffle2["in1"].setValue(layer_name)
        shuffle2["label"].setValue(layer_name)

        premult = nuke.nodes.Premult(inputs=[shuffle2])
        premult.setXYpos(shuffle2.xpos(), shuffle2.ypos() + 80)

        premult_nodes.append(premult)

    return premult_nodes


def _get_exr_layers(exr_node):
    """
    Liste les layers disponibles dans un EXR, en excluant les layers techniques.
    Preserve l'ordre d'apparition dans le fichier (fond -> premier plan).
    """
    channels = exr_node.channels()
    seen = set()
    layers = []
    for ch in channels:
        layer = ch.split(".")[0]
        if layer.lower() not in EXCLUDE_LAYERS and layer not in seen:
            seen.add(layer)
            layers.append(layer)

    return layers
