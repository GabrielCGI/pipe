
# standard deps
from pathlib import Path
import logging
import glob
import os
import re

# package deps
from . import assetitem as at
import importlib
importlib.reload(at)

#import USD libs
try:
    from pxr import UsdUtils, Sdf, Ar
except:
    pass

logger = logging.getLogger(__name__)

SHOW_LOGS = False


class USDParser():
    
    def __init__(self, log_func=None):
        self._assets_to_update: list[at.AssetItem] = []
        self.__log_func = log_func
        if not self.__log_func:
            self.__log_func = print
        self.ar_context = ["I:/", "R:/"]
        self._enable_update = True
            
            
    def get_assets_to_update(self) -> list[at.AssetItem]:
        return list(self._assets_to_update)
    
    
    def set_assets_to_update(self, assets_to_update:list[at.AssetItem]):
        self._assets_to_update = assets_to_update


    def _log(self, txt: str):
        if SHOW_LOGS:
            self.__log_func(txt)
        
                
    # ---------------------------------Utils---------------------------------
    
    def _resolve_path(self, assetPathProcessed: str) -> Path:
            asset_path = Path(assetPathProcessed)
            if asset_path.is_absolute():
                return asset_path.resolve()
            else:
                relative_to_layer_path = self.dirname / asset_path
                if relative_to_layer_path.exists():
                    return relative_to_layer_path.resolve()
                try:
                    resolver = Ar.GetResolver()
                    resolved_path = resolver.Resolve(assetPathProcessed)
                    resolved_path = resolved_path.GetPathString()
                    if os.path.exists(resolved_path):
                        return Path(resolved_path)
                    resolved_path = Path(resolved_path)
                    parent_path = Path(*resolved_path.parts[:2])
                    parent_resolved = resolver.Resolve(parent_path.as_posix())
                    parent_resolved = parent_resolved.GetPathString()
                    if os.path.exists(parent_resolved):
                        return (Path(parent_resolved).parts[0]
                                / Path(*resolved_path.parts[1:]))
                except Exception as e:
                    logger.warning(e)
                return relative_to_layer_path
            
    
    def _add_item_list_once(self, item: at.AssetItem):
        # add item to update list if new
        if (item not in self._assets_to_update):
            self._assets_to_update.append(item)
        
    
    def _add_item_list_abs(self, item: at.AssetItem):
        # add item to update list if new and absolute
        if (item not in self._assets_to_update
            and os.path.isabs(item.original_path)):
            self._assets_to_update.append(item)
        
            
    # -------------------------------Parse USD-------------------------------
        
    def _parse_filter(self, assetPathProcessed): 
        logger.debug(f'Parse {assetPathProcessed}')
        
        # resolve path from context or layer if needed
        resolved_path = self._resolve_path(assetPathProcessed)
        if len(resolved_path.parts) < 2:
            logger.debug(' - path is too short')
            return assetPathProcessed
        
        # create item
        relative_path = Path(*resolved_path.parts[1:])
        item = at.AssetItem(
            assetPathProcessed,
            relative_path.as_posix(),
            None,
            None
        )
        item.layer_path = Path(self.previousLayer.realPath).as_posix()
        item.can_be_updated = self._enable_update
        
        # check extension for USD files
        extension = resolved_path.suffix
        if not extension in ['.usdc', '.usda']:
            logger.debug(' - not an USD file')
            self._add_item_list_abs(item)
            return assetPathProcessed
        
        # parse alternate versions paths
        glob_pattern = (
            re
            .sub(r'v\d{2,9}', 'v*', resolved_path.as_posix())
            .replace(extension, '.usd*')
        )
        glob_versions = glob.glob(glob_pattern)
        
        versions = []
        for version in glob_versions:
            if not '.bak' in version:
                versions.append(version)
        
        versions.sort()
        if not versions:
            self._log(
                f"❌ Did not found others versions: {assetPathProcessed}"
            )
            logger.debug(' - did not found others versions')
            self._add_item_list_abs(item)
            return assetPathProcessed
        
        # parse versions digits
        version_pattern = r'.*?v(\d{2,9}).*?'
        latest_match = re.search(version_pattern, versions[-1])
        current_match = re.search(version_pattern, assetPathProcessed)
        if not current_match or not latest_match:
            self._log(
                f"❌ Skipped (invalid or unresolvable): {assetPathProcessed}"
            )
            logger.debug(' - skipped (invalid or unresolvable)')
            self._add_item_list_abs(item)
            return assetPathProcessed
        
        # check if the current asset is the latest
        latest_version = int(latest_match.group(1))
        current_version = int(current_match.group(1))
        if latest_version == current_version:
            logger.debug(' - Already updated')
            self._log(f"🟰 Skipping up-to-date: {assetPathProcessed}")
            self._add_item_list_abs(item)
            return assetPathProcessed
            
        # update item to show latest and current version
        logger.debug(' - Can be updated')
        if not Path(assetPathProcessed).is_absolute():
            updatedPath = re.sub(
                r'v\d{2,9}', f'v{latest_match.group(1)}',
                assetPathProcessed
            )
        else:
            updatedPath = re.sub(
                r'v\d{2,9}', f'v{latest_match.group(1)}',
                relative_path.as_posix()
            )
        latest_extension = os.path.splitext(versions[-1])[1]
        updatedPath = os.path.splitext(updatedPath)[0] + latest_extension
        
        item.updated_path = updatedPath
        item.from_version = current_version
        item.to_version = latest_version
        self._add_item_list_once(item)
        return assetPathProcessed


    def _apply_parse_filter(self, layer, depInfos):
        if layer.identifier == self.previousLayer.identifier:
            return depInfos
        path = layer.resolvedPath.GetPathString()
        if not path:
            return depInfos
        self.dirname = Path(path).parent
        self.previousLayer = layer
        UsdUtils.ModifyAssetPaths(layer, self._parse_filter)
        self.dirname = ''
        return depInfos


    def _parse_dependencies(self, layer):
        self.previousLayer = layer
        UsdUtils.ModifyAssetPaths(layer, self._parse_filter)
        

    def _recursive_parse_dependencies(self, layer):
        self._enable_update = False
        self.previousLayer = layer
        UsdUtils.ModifyAssetPaths(layer, self._parse_filter)
        UsdUtils.ComputeAllDependencies(
            layer.identifier,
            self._apply_parse_filter
        )    
        self._enable_update = True
        

    def parse(self, layer: Sdf.Layer , enable_recursion: bool=False):
        self._assets_to_update.clear()
        ar_context = Ar.DefaultResolverContext(self.ar_context)
        with Ar.ResolverContextBinder(ar_context):
            self.dirname = Path((layer.realPath)).parent
            if enable_recursion:
                logger.debug('Start recursive parsing')
                self._recursive_parse_dependencies(layer)
            else:
                logger.debug('Start normal parsing')
                self._parse_dependencies(layer)
            self.dirname = ''    


    # -------------------------------Update USD-------------------------------

    def _update_filter(self, assetPathProcessed):
        asset_path = Path(assetPathProcessed)
        extension = asset_path.suffix
        
        # remove drive if the path has a drive to help ar resolver 
        if asset_path.is_absolute() and len(asset_path.parts) > 2:
            asset_path = Path(*asset_path.parts[1:]).as_posix()
        else:
            asset_path = assetPathProcessed
            
        if not extension in ['.usdc', '.usda']:
            return asset_path
        
        # check if the assetPathProcessed should be update
        for item in self._assets_to_update:
            if not item.can_be_updated:
                continue
            if not item.should_be_updated:
                continue
            if item.original_path == assetPathProcessed:
                self._log(
                    f"✅ Updated: {item.original_path} "
                    f"→ {item.updated_path}"
                )
                self.changed = True
                return item.updated_path

        return asset_path


    def _apply_update_filter(self, layer, depInfos):
        if layer.identifier == self.previousLayer.identifier:
            return depInfos
        path = layer.resolvedPath.GetPathString()
        if not path:
            return depInfos
        self.previousLayer = layer
        self.changed = False
        UsdUtils.ModifyAssetPaths(layer, self._update_filter)
        if self.changed:
            layer.Save()
            logger.debug("Update complete.")
            self._log("🎉 Update complete.")
        else:
            logger.debug("Nothing to update.")
            self._log("✅ Nothing to update.")
        self.changed = False
        return depInfos


    def update_layer(self, layer):
        logger.debug('Updating ...')
        self.changed = False
        UsdUtils.ModifyAssetPaths(layer, self._update_filter)
        if self.changed:
            layer.Save()
            logger.debug("Update complete.")
            self._log("🎉 Update complete.")
        else:
            logger.debug("Nothing to update.")
            self._log("✅ Nothing to update.")
        layer.Save()
        logger.debug('Update saved')
        self.changed = False


    def recursive_update(self, layer):
        self.changed = False
        UsdUtils.ModifyAssetPaths(layer, self._update_filter)
        changed = self.changed
        self.previousLayer = layer
        UsdUtils.ComputeAllDependencies(
            layer.identifier,
            self._apply_update_filter
        )
        if changed:
            layer.Save()
            self._log("🎉 Update complete.")
        else:
            self._log("✅ Nothing to update.")
        self.changed = False


    # --------------------OLD Parse And Update (USDA only)--------------------

    def parse_payloads(self, content):
        self._assets_to_update.clear()
        
        # Simplified: focus only on @...usd[ac]@
        pattern = r"@[^@]+\.usd[ac]@(?:<[^>]+>)?"  
        matches = re.findall(pattern, content, re.IGNORECASE)
        seen = set()
        self._log(f"Found {len(matches)} payload(s)")
        
        for m in matches:
            # Remove optional target path
            clean_path = re.sub(r"<[^>]+>$", "", m) 
            m_norm = clean_path.lower()
            if m_norm in seen:
                continue
            seen.add(m_norm)
            item = self.find_latest_version_path(clean_path)
            if item:
                if item.from_version != item.to_version:
                    self._add_item_list_once(item)
                else:
                    self._log(
                        f"🟰 Skipping up-to-date: {item.original_path}"
                    )
            else:
                self._log(
                    f"❌ Skipped (invalid or unresolvable): {clean_path}"
                )
                
                
    def find_latest_version_path(self, original_path):
        path_pattern = (
            r"@(?P<base>.+?/Export/.+?/)"
            r"v(?P<version>\d{3})/"
            r"(?P<asset_name>.+)_.+?_"
            r"(v\d{3}\.usd[ac])@"
        )
        match = re.match(
            path_pattern,
            original_path,
            re.IGNORECASE
        )
        if not match:
            return None

        base_dir = match.group("base").replace("/", os.sep)
        current_version = int(match.group("version"))
        asset_name = match.group("asset_name")

        if not os.path.exists(base_dir):
            return None

        versions = [int(folder[1:]) for folder in os.listdir(base_dir)
                    if re.fullmatch(r"v\d{3}", folder)]
        if not versions:
            return None

        latest_version = max(versions)
        latest_str = f"v{latest_version:03d}"
        latest_folder = os.path.join(base_dir, latest_str)

        for fname in os.listdir(latest_folder):
            fullmatch = re.fullmatch(
                f"{re.escape(asset_name)}_.+?_{latest_str}\\.usd[ac]",
                fname,
                re.IGNORECASE
            )
            if fullmatch:
                latest_path = f"@{match.group('base')}/{latest_str}/{fname}@"
                return at.AssetItem(
                    original_path,
                    latest_path,
                    current_version,
                    latest_version
                )
        return None
