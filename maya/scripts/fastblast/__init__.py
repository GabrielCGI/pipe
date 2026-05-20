from . import fast_blast, fast_blast_UI, get_shotlist
from importlib import reload

def main() -> None:
    
    reload(fast_blast)
    reload(fast_blast_UI)
    reload(get_shotlist)

    fast_blast_UI.run_ui()
