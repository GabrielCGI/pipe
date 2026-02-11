import socket


from . import gui
from . import texture_parser

from importlib import reload

reload(gui)
reload(texture_parser)

def run():
    # if socket.gethostname() == "SPRINTER-04" : 
    #     from . import debug
    #     debug.debug()
    gui.run()
