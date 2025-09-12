from pxr import Usd, Sdf, Ar
import hou

stage = hou.pwd().editableStage()

# --- helpers ---
def ensure_attr(prim, name, type_name, default_val=None):
    if prim.HasAttribute(name):
        a = prim.GetAttribute(name)
        if a.GetTypeName() != type_name:
            prim.RemoveProperty(name)
    attr = prim.CreateAttribute(name, type_name)
    if default_val is not None:
        attr.Set(default_val)
    return attr

resolver = Ar.GetResolver()
def layer_abs_path(layer):
    if not layer:
        return ""
    # 1) Essayer realPath (souvent déjà absolu)
    rp = getattr(layer, "realPath", "") or ""
    if rp:
        return rp
    # 2) Essayer via le resolver
    resolved = resolver.Resolve(layer.identifier) or ""
    return resolved

# --- Render Product ---
renderproduct = stage.GetPrimAtPath("/Render/Products/renderproduct")
if not renderproduct or not renderproduct.IsValid():
    raise RuntimeError("Render Product introuvable: /Render/Products/renderproduct")

# Attribut metadata string qui contiendra le chemin
meta_cam_layer_attr = ensure_attr(
    renderproduct,
    "driver:parameters:OpenEXR:cameraLayerPath",
    Sdf.ValueTypeNames.String,
    ""
)

# --- Camera prim (shape) ---
camera_path = "/cameras/camRig/camera/shotCam"
camera_prim = stage.GetPrimAtPath(camera_path)
if not camera_prim or not camera_prim.IsValid():
    raise RuntimeError(f"Prim caméra introuvable: {camera_path}")

# --- Trouver le layer "def" le plus fort qui définit la caméra ---
def_layer = None
for ps in camera_prim.GetPrimStack():
    if ps.specifier == Sdf.SpecifierDef:
        def_layer = ps.layer
        break

# Résoudre chemin absolu (ou fallback sur identifier si non résoluble/anonyme)
abs_path = layer_abs_path(def_layer)
if not abs_path and def_layer:
    abs_path = def_layer.identifier  # ex: anon:... ou URL du resolver

# Stocker dans la metadata
meta_cam_layer_attr.Set(abs_path)
