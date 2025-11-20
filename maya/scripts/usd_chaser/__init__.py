from importlib import reload



def chaser_layer_anim(*args):
    from . import usd_chaser_anim
    reload(usd_chaser_anim)
    return usd_chaser_anim.main(*args)

def create_inheriteClass(*args):
    from . import usd_chaser_anim
    reload(usd_chaser_anim)
    return usd_chaser_anim.startInheriteClass(*args)