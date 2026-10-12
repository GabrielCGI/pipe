"""v1 compatibility shim — the precomp system is now src/precomp (v2).

Scripts saved with the v1 setup still reference this module from knob
expressions (`precomp_which`) and buttons (`hasher`) until they are
upgraded (Render Manager > Upgrade Precomps). Every entry point here is
side-effect free: a v1 switch always routes live (correct pixels, no
caching) and nothing is written to disk.
"""


def precomp_which(switch_node):
    return 1


def upstream_hash(write_node):
    return None


def _atomic_json(path, data):
    pass


def refresh_precomps():
    """Former "Shot Loader > Refresh Precomps" command (personal menus may
    still call it)."""
    from src.precomp import engine
    print(engine.report(engine.sync()))
