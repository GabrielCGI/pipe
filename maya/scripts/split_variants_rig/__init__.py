
from importlib import reload



def main(*args):
    from . import splits_variants_rig
    reload(splits_variants_rig)
    return splits_variants_rig.splitVariantsRig(*args)

def controler(*args):
    from . import controler_for_select_variant
    reload(controler_for_select_variant)
    return controler_for_select_variant.run(*args)