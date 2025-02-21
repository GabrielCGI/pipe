from pxr import UsdGeom, Usd, Gf
import hou

def set_data_window_ndc(render_settings_node_path, cube_prim_path, camera_prim_path):
    # Get the stage from the input
    stage = hou.node(render_settings_node_path).inputs()[0].stage()

    # Create a BBoxCache for efficient bounding box calculation
    bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode(0), [UsdGeom.Tokens.default_])

    # Get the camera and cube primitives
    camera_prim = stage.GetPrimAtPath(camera_prim_path)
    cube_prim = stage.GetPrimAtPath(cube_prim_path)

    # Ensure both camera and cube exist
    if not camera_prim or not cube_prim:
        raise ValueError("Camera or Cube not found in the stage.")

    # Get the camera object
    camera = UsdGeom.Camera(camera_prim)

    # Get camera attributes
    focal_length = camera.GetFocalLengthAttr().Get()
    aperture_x = camera.GetHorizontalApertureAttr().Get()
    aperture_y = camera.GetVerticalApertureAttr().Get()

    # Get the cube's world-space bounding box
    bbox = bbox_cache.ComputeWorldBound(cube_prim)
    bbox_range = bbox.GetRange()
    min_bound = bbox_range.GetMin()
    max_bound = bbox_range.GetMax()

    # Get the camera's world transform
    camera_transform = UsdGeom.Xformable(camera_prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    camera_transform_inv = camera_transform.GetInverse()

    # Transform the bounding box corners
    corners = [
        Gf.Vec3d(min_bound[0], min_bound[1], min_bound[2]),
        Gf.Vec3d(max_bound[0], min_bound[1], min_bound[2]),
        Gf.Vec3d(min_bound[0], max_bound[1], min_bound[2]),
        Gf.Vec3d(max_bound[0], max_bound[1], min_bound[2]),
        Gf.Vec3d(min_bound[0], min_bound[1], max_bound[2]),
        Gf.Vec3d(max_bound[0], min_bound[1], max_bound[2]),
        Gf.Vec3d(min_bound[0], max_bound[1], max_bound[2]),
        Gf.Vec3d(max_bound[0], max_bound[1], max_bound[2]),
    ]

    # Transform corners into camera space and project into NDC space
    ndc_coords = []

    for corner in corners:
        # Transform to camera space
        camera_space_point = camera_transform_inv.Transform(corner)

        # Skip points behind the camera (positive Z in camera space)
        if camera_space_point[2] >= 0:
            continue

        # Perspective projection calculation
        ndc_x = (camera_space_point[0] * focal_length) / (abs(camera_space_point[2]) * (aperture_x * 0.5)) * 0.5 + 0.5
        ndc_y = (camera_space_point[1] * focal_length) / (abs(camera_space_point[2]) * (aperture_y * 0.5)) * 0.5 + 0.5

        ndc_coords.append((ndc_x, ndc_y))

    # Compute the min and max bounds in NDC space
    if ndc_coords:
        min_x = min(coord[0] for coord in ndc_coords)
        min_y = min(coord[1] for coord in ndc_coords)
        max_x = max(coord[0] for coord in ndc_coords)
        max_y = max(coord[1] for coord in ndc_coords)

        # Set the Data Window NDC values in the render settings node
        render_node = hou.node(render_settings_node_path)
        render_node.parm("dataWindowNDC1").set(min_x)
        render_node.parm("dataWindowNDC2").set(min_y)
        render_node.parm("dataWindowNDC3").set(max_x)
        render_node.parm("dataWindowNDC4").set(max_y)

        print("Data Window NDC updated successfully!")
    else:
        print("The cube is not visible in the camera frustum.")


# Example usage:
# Set paths based on your current scene setup
render_settings_node_path = "/stage/rendersettings_edit6"
cube_prim_path = "/cube1"
camera_prim_path = "/cameras/camera1"

# Call the function to update the Data Window NDC
set_data_window_ndc(render_settings_node_path, cube_prim_path, camera_prim_path)
