import houdinilog
import hou

# Standard lib
import os
import time

# Interface lib
import tkinter as tk

"""
WIP
"""

class Application(tk.Tk):

    """Basic application with tkinter"""

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        # Title
        self.title('Photomosaic')

        # Resolution
        self.geometry("854x480")
        self.minsize(426, 240)
        self.maxsize(1280, 720)
        
        
        # Initialize the main frame 
        self.scene_initializer()

    def scene_initializer(self):
        """ Load a main frame."""

        main_frame = tk.Frame(self)

        shaders_select_frame = tk.Frame(self)
        
        main_frame.pack()


def main():
    app = Application()
    app.mainloop()