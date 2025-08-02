import shutil
from datetime import datetime
from pxr import Usd
from pathlib import Path


def cleanAttribute(product_directory: str):
    
    usd_dir = Path(product_directory)
    mtl_path = None
    for path in usd_dir.glob('mtl.usd*'):
        mtl_path = path
        break
    if not mtl_path:
        print(f'Did not found mtl.usd file in {usd_dir}')
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{mtl_path}.{timestamp}.bak"
    try:
        shutil.copy2(mtl_path, backup_path)
    except Exception as e:
        print(f'Could not create a backup of {mtl_path}:\n{e}')
        return
    stage = Usd.Stage.Open(mtl_path.as_posix())
    cleanUSD(stage, "inputs:roughness")


def cleanUSD(stage, attributes_name):
    """
    Clean USD connections of specified usd_path prim in an
    USD stage.

    Args:
        stage (Usd.Stage): USD stage to clean.
        usd_path (str): Path to prim to clean.
        product_directory (str): USD Product directory.
    """
    
    root_prim = stage.GetPrimAtPath('/')
    prim_iterator = iter(Usd.PrimRange(root_prim))
    prim_to_clean = []
    for prim in prim_iterator:
        prim_basename = prim.GetPath().name
        if prim_basename == 'mtlxstandard_preview':
            prim_to_clean.append(prim)
            
        if ('mtlxstandard_preview' in prim_basename
            and 'roughness' in prim_basename):
            prim.SetActive(False)
            
    for prim in prim_to_clean:
        if prim and prim.IsValid():
            rough_attr = prim.GetAttribute(attributes_name)
            vec_connection = rough_attr.GetConnections()
            for p in vec_connection:
                rough_attr.RemoveConnection(p)
            rough_attr.Set(0.5)
    stage.Save()
    
if __name__ == '__main__':
    import os
    prod_dir = os.path.dirname(__file__)
    cleanAttribute(prod_dir)