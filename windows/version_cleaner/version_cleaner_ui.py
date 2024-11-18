
# Standard lib
import os
import time
import logging

# Interface lib
import tkinter as tk
import tkinter.scrolledtext as scrolledtext
from tkinter.filedialog import askdirectory

# Cleaner lib
import version_cleaner

"""
WORK IN PROGRESS .......................
"""

BACKGROUND_COLOR = "#FFFFFF"

class InitialPage(tk.Tk):
    
    """ Page to choose folder and settings  """
    
    def __init__(self):
        super().__init__()
        
        ## Window settings
        # Title
        self.title('Version Cleaner - Select Folder')
        self.minsize(500, 150)
        self.maxsize(550, 200)
        
        self.spinbox_var = tk.IntVar()
        
        mainFrame = tk.Frame(self, bg=BACKGROUND_COLOR)
        
        grid_folder = tk.Frame(mainFrame)
        label_folder = tk.Label(grid_folder,\
            text="Choose a folder to clean:")
        label_folder.grid(column=0, row=0)
        
        self.text_folder = tk.Entry(grid_folder, width=70)
        self.text_folder.grid(column=0, row=1)
        
        button_folder = tk.Button(grid_folder, text="...",\
            command=self.open_dir)
        button_folder.grid(column=1, row=1)
            
        versions_grid = tk.Frame(mainFrame)
        label_ask_versions = tk.Label(versions_grid,\
            text="How many version per objects do you want to save?")
        label_ask_versions.grid(column=0, row=0)
        
        label_versions = tk.Label(versions_grid,\
            text="Number of versions to save:")
        label_versions.grid(column=0, row=1)
        
        self.spinbox_versions = tk.Spinbox(versions_grid,\
            from_=0, to=1000, textvariable=self.spinbox_var)
        self.spinbox_versions.grid(column=1, row=1)
    
        confirm_frame = tk.Frame(mainFrame)
        
        button_confirm = tk.Button(confirm_frame, text="Valider",\
            command=self.open_app)
        button_confirm.pack()
        
        grid_folder.pack(side="top", fill='x')
        confirm_frame.pack(side="bottom", fill='x')
        versions_grid.pack(side="bottom", fill='x')
        
        mainFrame.pack(pady=10)
    
    def open_dir(self):
        """Open a folder """

        path = askdirectory()

        if not path:
            return

        self.text_folder.delete(0, 'end')
        self.text_folder.insert(0, path)
        
    def open_app(self):
        Application(self.text_folder.get(), int(self.spinbox_var.get()))
        self.destroy()

class LogHandler(logging.Handler):

    def __init__(self, text):
        logging.Handler.__init__(self)
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            self.text.yview(tk.END)
        self.text.after(0, append)


class Application(tk.Tk):

    """Basic application with tkinter"""

    def __init__(self, folder: str, versions_to_save: int):
        
        super().__init__()
        
        self.folder = folder
        self.versions_to_save = versions_to_save
        self.cleaner = version_cleaner.Cleaner(self.folder,\
            self.versions_to_save)
        
        # Title
        self.title('Version Cleaner')
        
        # Resolution
        self.minsize(500, 400)
        self.maxsize(550, 400)
        
        
        mainFrame = tk.Frame(self, bg=BACKGROUND_COLOR)
        mainFrame.grid(row=0, column=0, sticky="nsew")
        
        grid_parse = tk.Frame(mainFrame, bg="#FF0000")
        
        label_parse = tk.Label(grid_parse,\
            text=f"Chosen folder: {self.folder}",
            width=70)
        label_parse.grid(column=0, row=0)
        
        button_parse = tk.Button(grid_parse, text="Parse",\
            command=self.cleaner.retrieveVersionToFlag)
        button_parse.grid(column=1, row=0)
        
        grid_parse.pack(side="top", fill="x")
        
        # Log displayer
        
        self.log = tk.StringVar()
        self.log.set("En attente ...")
        
        logFrame = tk.Frame(mainFrame, bg="#0000FF")
        scrollText = scrolledtext.ScrolledText(logFrame, state="disabled")
        scrollText.configure(font='TkFixedFont')
        scrollText.pack(side="top", fill="both", expand=True)
        
        logLabel = tk.Label(logFrame, textvariable=self.log)
        logLabel.pack(side="bottom", fill="x")
        
        logHandler = LogHandler(scrollText)
        
        version_cleaner.LOG.addHandler(logHandler)

if __name__ == "__main__":
    app = InitialPage()
    app.mainloop()
