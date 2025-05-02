from ..tool_models.ActionTool import *
from pxr import Usd, UsdShade, Sdf
import maya.cmds as cmds
import mayaUsd.lib as mayaUsdLib


class FixUsdColorspaceManagement(ActionTool):
    def __init__(self):
        super().__init__(name="Fix Usd ColorspaceManagement",
                         pref_name="FixUsdColorspaceManagement",
                         description="Fix Usd colorspace management perpetual evaluation",
                         button_text="fix")

    def _action(self):
        """
        Set all colorspace in UsdUVTexture node to Raw
        """
        try:
            self.set_source_color_space_raw_on_usd_uv_textures()
        except Exception as e:
            print(str(e), warning=True)

    def set_source_color_space_raw_on_usd_uv_textures(self):
        # Try to use selected mayaUsdProxyShape
        selection = cmds.ls(selection=True, type="mayaUsdProxyShape", long=True)

        if not selection:
            # Fallback: find first mayaUsdProxyShape in scene
            all_proxies = cmds.ls(type="mayaUsdProxyShape", long=True)
            if not all_proxies:
                raise RuntimeError("No mayaUsdProxyShape found in the scene.")
            proxy_shape = all_proxies[0]
            print(f"No selection. Using first mayaUsdProxyShape found: {proxy_shape}")
        else:
            proxy_shape = selection[0]
            print(f"Using selected mayaUsdProxyShape: {proxy_shape}")

        usd_prim = mayaUsdLib.GetPrim(proxy_shape)
        if not usd_prim or not usd_prim.IsValid():
            raise RuntimeError("Invalid USD prim.")

        stage = usd_prim.GetStage()
        if not stage:
            raise RuntimeError("Could not retrieve USD stage from mayaUsdProxyShape.")

        updated_count = 0
        skipped_count = 0

        def recurse_and_tag_uv_textures(prim):
            nonlocal updated_count, skipped_count
            if prim.GetTypeName() == "Shader":
                shader = UsdShade.Shader(prim)
                if shader and shader.GetIdAttr().Get() == "UsdUVTexture":
                    input_attr = shader.GetInput("sourceColorSpace")
                    if input_attr:
                        current_val = input_attr.Get()
                        if current_val != "auto":
                            skipped_count += 1
                            return
                        else:
                            input_attr.Set("raw")
                    else:
                        shader.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.String).Set("raw")
                    updated_count += 1

            for child in prim.GetChildren():
                recurse_and_tag_uv_textures(child)

        recurse_and_tag_uv_textures(stage.GetPseudoRoot())
        print(f"Updated {updated_count} UsdUVTexture node(s). Skipped {skipped_count} already set to 'raw'.")
