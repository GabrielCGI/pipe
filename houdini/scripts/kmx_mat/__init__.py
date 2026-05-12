def kmxchar_execute():
    from . import kmx_char 
    kmx_char.execute()

def kmfa_execute(collectionMode=True, sel=None):
    from . import kma_mat_from_attr
    kma_mat_from_attr.execute(collectionMode=collectionMode, sel=sel)