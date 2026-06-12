"""
card_builder.py
Creation d'un Card2 dont la position et la taille sont pilotees
par un controleur de profondeur (NoOp avec slider).

Les knobs translate et scaling du Card2 contiennent des expressions
qui referencent le knob 'depth_value' du NoOp controleur.
Modifier le slider repositionne et redimensionne le card en temps reel.

Formules :
  - Position   : card_translate = cam_pos + depth * forward_vec
  - Taille     : width  = (haperture / focal) * depth * OVERSCAN * scale_mult
                 height = width / image_aspect * OVERSCAN * scale_mult

Note Camera4 USD : les knobs translate/rotate sont locaux (= 0).
On utilise le knob world_matrix qui retourne la matrice monde correcte.
"""

import nuke
import math

OVERSCAN = 1.5


def build_card(camera_node, premult_node, depth_ctrl_noop, depth_knob_name,
               layer_name, proj_camera=None):
    """
    Cree un Project3D -> Card2 pour un calque PSD.

    Position et taille sont liees au NoOp global via expressions
    sur le knob depth_knob_name.

    Args:
        camera_node      : Camera node (pour intrinsics et position)
        premult_node     : Premult node du calque PSD
        depth_ctrl_noop  : NoOp global contenant tous les sliders de profondeur
        depth_knob_name  : nom du knob dans le NoOp pour ce calque
        layer_name       : nom du layer PSD (pour nommer le Card2)
        proj_camera      : node branche en input 1 du Project3D (FrameHold).
                           Si None, utilise camera_node directement.

    Retourne le Card2 node.
    """
    cam_pos, forward_vec = _get_camera_transform(camera_node)
    focal     = camera_node["focal"].getValue()
    haperture = camera_node["haperture"].getValue()

    if focal <= 0:
        nuke.warning("card_builder: focal invalide ({}) -- fallback 50.".format(focal))
        focal = 50.0

    # Ratio image reel (pixels) pour la hauteur du card
    fmt = nuke.root().format()
    img_aspect = float(fmt.width()) / float(fmt.height())

    ctrl = depth_ctrl_noop.name()
    knob = depth_knob_name

    # -- Project3D : projette la texture depuis l'angle exact de la camera -----
    cam_for_proj = proj_camera if proj_camera is not None else camera_node
    project3d = nuke.nodes.Project3D(inputs=[premult_node, cam_for_proj])

    # -- Card2 -----------------------------------------------------------------
    card = nuke.nodes.Card2(inputs=[project3d])
    card.setName("{}_card".format(layer_name))

    # Translate : cam_pos + depth * forward_vec  (expression par axe)
    card["translate"].setExpression(
        "{:.6f} + {}.{} * ({:.6f})".format(cam_pos[0], ctrl, knob, forward_vec[0]), 0)
    card["translate"].setExpression(
        "{:.6f} + {}.{} * ({:.6f})".format(cam_pos[1], ctrl, knob, forward_vec[1]), 1)
    card["translate"].setExpression(
        "{:.6f} + {}.{} * ({:.6f})".format(cam_pos[2], ctrl, knob, forward_vec[2]), 2)

    # Scaling : width  = (haperture / focal) * depth * overscan * scale_mult
    #           height = width / image_aspect
    w_factor = (haperture / focal) * OVERSCAN
    h_factor = w_factor / img_aspect

    card["scaling"].setExpression(
        "{:.6f} * {}.{} * {}.scale_mult".format(w_factor, ctrl, knob, ctrl), 0)
    card["scaling"].setExpression(
        "{:.6f} * {}.{} * {}.scale_mult".format(h_factor, ctrl, knob, ctrl), 1)

    # Rotation : vertical par defaut (debout, tourne en Y vers la camera)
    _, ry, _ = _forward_to_euler(forward_vec)
    card["rotate"].setValue([0.0, ry, 0.0])

    return card


def get_card_rotations(camera_node):
    """
    Retourne les deux modes de rotation pour les cards :
      face_cam : perpendiculaire a l'axe de visee (rx, ry, 0)
      vertical : debout dans le monde, tourne en Y vers la camera (0, ry, 0)
    """
    _, forward_vec = _get_camera_transform(camera_node)
    face_cam = _forward_to_euler(forward_vec)
    vertical = [0.0, face_cam[1], 0.0]
    return face_cam, vertical


# -- Fonctions utilitaires camera ----------------------------------------------

def _get_camera_transform(camera_node):
    """
    Lit la position monde et le vecteur forward de la camera.

    Priorite :
      1. Knob 'world_matrix' (Array_Knob 4x4, Camera4 USD etc.)
      2. Fallback : knobs translate + rotate (Camera2 / Camera3)

    Retourne : (cam_pos [x,y,z], forward_vec [x,y,z])
    """
    world_matrix_knob = camera_node.knob("world_matrix")
    if world_matrix_knob is not None:
        m = [world_matrix_knob.getValue(i) for i in range(16)]
        cam_pos = [m[3], m[7], m[11]]
        fx, fy, fz = -m[2], -m[6], -m[10]
    else:
        t = camera_node["translate"].value()
        cam_pos = [t[0], t[1], t[2]]
        rx_deg = camera_node["rotate"].getValue(0)
        ry_deg = camera_node["rotate"].getValue(1)
        fx, fy, fz = _euler_to_forward(rx_deg, ry_deg)

    length = math.sqrt(fx*fx + fy*fy + fz*fz)
    if length > 0:
        fx, fy, fz = fx/length, fy/length, fz/length

    return cam_pos, [fx, fy, fz]


def _euler_to_forward(rx_deg, ry_deg):
    """
    Calcule le vecteur forward depuis les angles Euler pitch (rx) et yaw (ry).
    La camera regarde dans la direction -Z en espace local.
    """
    rx = math.radians(rx_deg)
    ry = math.radians(ry_deg)
    fx =  math.cos(rx) * math.sin(ry)
    fy = -math.sin(rx)
    fz = -math.cos(rx) * math.cos(ry)
    return fx, fy, fz


def _forward_to_euler(forward_vec):
    """
    Calcule les angles Euler (rx, ry) du Card2 depuis le vecteur forward,
    de sorte que le card soit perpendiculaire a l'axe de visee.
    """
    fx, fy, fz = forward_vec
    rx = math.degrees(math.asin(max(-1.0, min(1.0, fy))))
    ry = math.degrees(math.atan2(-fx, -fz))
    return [rx, ry, 0.0]
