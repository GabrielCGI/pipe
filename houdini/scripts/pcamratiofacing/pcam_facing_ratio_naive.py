
from pxr import Usd, UsdGeom, Gf, Sdf
import hou
import math
import logging

logger = logging.getLogger(__name__)

# Projection function
def pinhole_uv_projection(camera_inv_matrix, points, focal_mm, filmback_mm_x, filmback_mm_y):
    half_fov_x = math.atan2(filmback_mm_x * 0.5, focal_mm)
    half_fov_y = math.atan2(filmback_mm_y * 0.5, focal_mm)
    uv_list = []
    for p_world in points:
        p_cam = camera_inv_matrix.Transform(p_world)
        z_cam = -p_cam[2]
        if abs(z_cam) < 1e-12:
            uv_list.append(Gf.Vec2f(0.5, 0.5))
            continue
        x_ratio = p_cam[0] / (-p_cam[2])
        y_ratio = p_cam[1] / (-p_cam[2])
        u = 0.5 + 0.5 * (x_ratio / math.tan(half_fov_x))
        v = 0.5 + 0.5 * (y_ratio / math.tan(half_fov_y))
        uv_list.append(Gf.Vec2f(u, v))
    return uv_list

# Facing ratio for point normals
def calculate_facing_ratio_vertex(camera_position, normals, points):
    facing_ratios = []
    for pt, normal in zip(points, normals):
        view_dir = Gf.Vec3f(camera_position - pt)
        view_dir.Normalize()
        dot = Gf.Dot(normal, view_dir)
        facing_ratios.append(max(0.0, min(1.0, dot)))
    return facing_ratios


def calculate_facing_ratio_faceVarying(camera_position, normals, face_vertex_indices, points):
    facing_ratios = [0.0] * len(points)
    count = [0] * len(points)

    for i, pt_idx in enumerate(face_vertex_indices):
        if pt_idx >= len(points):
            continue

        if i >= len(normals):
            print(f"[!] Warning: Normal index {i} out of range (len(normals) = {len(normals)})")
            continue

        pt = points[pt_idx]
        normal = Gf.Vec3f(normals[i])

        view_dir = Gf.Vec3f(camera_position - pt)
        view_dir.Normalize()
        dot = Gf.Dot(normal, view_dir)
        fr = max(0.0, min(1.0, dot))

        facing_ratios[pt_idx] += fr
        count[pt_idx] += 1

    for i in range(len(facing_ratios)):
        if count[i] > 0:
            facing_ratios[i] /= count[i]
        else:
            facing_ratios[i] = 0.0

    return facing_ratios


def main():
    node = hou.pwd()
    stage = node.editableStage()

    # Retrieve node parameters
    primpattern   = node.parm('primpat').eval()
    sourceframe   = int(node.parm('src_frame').eval())
    primvarname   = node.parm('attr_name').eval()
    camera_path   = node.parm('camera').eval()

    logger.info("=== Debug: Parameter Retrieval ===")
    logger.info(f"Prim Pattern: {primpattern}")
    logger.info(f"Source Frame: {sourceframe}")
    logger.info(f"Primvar Name: {primvarname}")
    logger.info(f"Camera Path : {camera_path}")

    # Validate camera
    camera_prim = stage.GetPrimAtPath(camera_path)
    if not camera_prim or not camera_prim.IsA(UsdGeom.Camera):
        raise ValueError(f"Invalid camera: {camera_path}")

    usd_camera       = UsdGeom.Camera(camera_prim)
    focal_length     = usd_camera.GetFocalLengthAttr().Get()
    h_aperture       = usd_camera.GetHorizontalApertureAttr().Get()
    v_aperture       = usd_camera.GetVerticalApertureAttr().Get()

    SCALE_TO_MM = 100.0
    focal_mm    = focal_length * SCALE_TO_MM
    haperture_mm= h_aperture  * SCALE_TO_MM
    vaperture_mm= v_aperture  * SCALE_TO_MM

    logger.info("=== Camera Debug ===")
    logger.info(f"Focal Length (mm)         : {focal_mm}")
    logger.info(f"Horizontal Aperture (mm)  : {haperture_mm}")
    logger.info(f"Vertical Aperture (mm)    : {vaperture_mm}")

    # Compute camera world transform
    timecode = Usd.TimeCode(sourceframe)
    camera_world_xf = UsdGeom.Xformable(usd_camera).ComputeLocalToWorldTransform(timecode)
    cam_no_scale = Gf.Matrix4d(camera_world_xf)
    camera_inv = cam_no_scale.GetInverse()
    # Select matching mesh prims
    lop_sel = hou.LopSelectionRule()
    lop_sel.setPathPattern(primpattern + " & %type:Mesh")
    matching_paths = lop_sel.expandedPaths(stage=stage)

    logger.info("=== Matching Meshes ===")
    for mp in matching_paths:
        logger.info(f"  {mp}")

    for primpath in matching_paths:
        prim = stage.GetPrimAtPath(primpath)
        if not prim or not prim.IsValid():
            logger.info(f"Skipping invalid prim: {primpath}")
            continue

        points_attr = prim.GetAttribute("points")
        normals_attr = prim.GetAttribute("normals")

        if not points_attr or not normals_attr:
            logger.info(f"Missing points or normals on {primpath}, skipping.")
            continue

        points_data = points_attr.Get(timecode)
        normals_data = normals_attr.Get(timecode)

        if not points_data or not normals_data:
            logger.info(f"Missing data on {primpath}, skipping.")
            continue

        obj_xform = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(timecode)
        points_world = [obj_xform.TransformAffine(Gf.Vec3d(p)) for p in points_data]
        camera_position = Gf.Vec3d(camera_world_xf[3][0], camera_world_xf[3][1], camera_world_xf[3][2])

        # --- Here is the interpolation check ---
        normal_interp = normals_attr.GetMetadata("interpolation")
        logger.info(normal_interp)
        
        if not normal_interp:
            logger.info(f"Could not determine normal interpolation on {primpath}, defaulting to 'point'")
            normal_interp = "vertex"

        if normal_interp == UsdGeom.Tokens.vertex:
            logger.info("vertex (point in Houdini) detected")
            normals_vec3 = [Gf.Vec3f(n) for n in normals_data]
            facing_ratios = calculate_facing_ratio_vertex(
                camera_position, normals_vec3, points_world)
        else:
            logger.info("faceVarying (vertex in Houdini) detected")
            mesh = UsdGeom.Mesh(prim)
            face_vertex_indices_attr = mesh.GetFaceVertexIndicesAttr()
            face_vertex_indices = face_vertex_indices_attr.Get(timecode)
            normals_vec3 = [Gf.Vec3f(n) for n in normals_data]
            facing_ratios = calculate_facing_ratio_faceVarying(
                camera_position, normals_vec3, face_vertex_indices, points_world)
            
                
        uv_out = pinhole_uv_projection(camera_inv, points_world,
                                    focal_mm, haperture_mm, vaperture_mm)
        facing_ratio_data = [Gf.Vec3f(uv[0], uv[1], facing_ratio) for uv, facing_ratio in zip(uv_out, facing_ratios)]

        primvars_api = UsdGeom.PrimvarsAPI(prim)
        primvar = primvars_api.CreatePrimvar(
            primvarname,
            Sdf.ValueTypeNames.Float3Array,
            UsdGeom.Tokens.vertex
        )
        primvar.Set(facing_ratio_data)

        logger.info(f"Created primvar '{primvarname}' on {primpath} with {len(facing_ratio_data)} items.")
