

class AssetItem():
    
    
    def __init__(
            self,
            original_path,
            updated_path,
            from_version,
            to_version):
        self.original_path = original_path
        self.updated_path = updated_path
        self.from_version = from_version
        self.to_version = to_version
        self.layer_path = None
        self.can_be_updated = True
        self.should_be_updated = True
        
        
    def __str__(self):
        asset_item_str = (
            f"{self.layer_path}:\n"
            f" - {self.original_path}\n"
            f" -> {self.updated_path}\n"
            f" - {self.from_version} -> {self.to_version}\n"
            f" - Should be updated : {self.should_be_updated}\n"
            f" - Can be updated : {self.can_be_updated}\n"
        )
        return asset_item_str