import socket

from . import gui
from . import texture_parser

from importlib import reload

reload(gui)
reload(texture_parser)

def run():
    gui.run()
    if socket.gethostname() == "SPRINTER-04" : 
        from . import debug
        debug.debug()

def test():
    #mat_find = USD_Material_Finder.MaterialFinder()
    tex_find = texture_parser.TextureParser()