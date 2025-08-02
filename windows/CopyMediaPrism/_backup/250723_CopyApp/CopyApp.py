import os
import glob
import json
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText

import file_utils


# Path for the configuration file
JSON_DIRECTORY = os.path.join(os.path.expanduser("~"), "Documents", "CopyApp")
JSON_DIRECTORY = "R:/pipeline/pipe/windows/CopyMediaPrism/configs"
config_file_path = "copy_config.json"

# Color configuration
BG_COLOR = "#434649"        # Background color
BUTTON_COLOR = "#797979"    # Button color
LOG_BG_COLOR = "#303030"    # Log background color
PROGRESS_BG = "#553F75"     # Progress bar background
PROGRESS_FG = "#1FDF1F"     # Progress bar progress color
TEXT_BG = "#303030"         # Text field background color
TEXT_FG = "#FFFFFF"         # Text color

# JSON KEYS
PRODUCTION_KEY = "production"
SOURCE_KEY = "source_path"
DEST_KEY = "dest_path"
FILTER_KEY = "filters"

# Function to load configuration
def load_config():
    config_path = os.path.join(JSON_DIRECTORY, config_file_path)
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

# Function to save configuration
def save_config(config):
    os.makedirs(os.path.dirname(JSON_DIRECTORY), exist_ok=True)
    config_path = os.path.join(JSON_DIRECTORY, config_file_path)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)


# Tkinter GUI setup
class CopyApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Media Copy Tool")
        self.root.geometry("1500x1100")
        self.root.configure(background=BG_COLOR)
        
        self.prod_name = tk.StringVar()
        self.preset_path = tk.StringVar()
        self.source_path = tk.StringVar()
        self.dest_path = tk.StringVar()
        
        # Load or create department identifiers JSON
        self.config = load_config()  # Load saved configuration
        self.department_identifiers = file_utils.load_or_create_department_identifiers()

        # Main layout
        self.main_frame = tk.Frame(root, bg=BG_COLOR)
        self.main_frame.pack(fill='both', expand=True)

        # Left side: Source, destination, exclusions, JSON editor, buttons
        left_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        # Right side: Log area
        self.right_frame = tk.Frame(self.main_frame, bg=BG_COLOR)
        self.right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # Frame for the JSON editor (taking half of the left column)
        json_frame = tk.Frame(left_frame, bg=BG_COLOR)
        json_frame.pack(pady=5, fill='x', expand=False)  # Not expanding to limit height

        tk.Label(json_frame, text="Department Identifiers (JSON):", fg=TEXT_FG, bg=BG_COLOR).pack(pady=5, fill='x')

        # Scrollable Text widget for displaying and editing the JSON content
        self.json_text = ScrolledText(json_frame, bg=TEXT_BG, fg=TEXT_FG) # self.json_text = ScrolledText(json_frame, height=10, bg=text_bg, fg=text_fg)
        self.json_text.pack(pady=5, fill='x', expand=True)

        # Load the current JSON content into the text widget
        self.load_json_content()

        # Button to save the modified JSON
        json_save_buttons = tk.Frame(json_frame, bg=BG_COLOR)
        json_save_buttons.pack(pady=5, fill='x', expand=False)

        tk.Button(json_save_buttons, text="Save", command=lambda: self.save_json_content(True), bg=BUTTON_COLOR, fg=TEXT_FG).pack(pady=5, fill='x')
        tk.Button(json_save_buttons, text="Save as new JSON", command=lambda: self.save_json_content(False), bg=BUTTON_COLOR, fg=TEXT_FG).pack(pady=5, fill='x')

        # Production name
        name_frame = tk.Frame(left_frame, bg=BG_COLOR)
        name_frame.pack(pady=0, fill='x', expand=True)
        
        tk.Label(name_frame, text='Production name:', fg=TEXT_FG, bg=BG_COLOR).pack(pady=0, fill='x')
        self.prodname_entry = tk.Entry(name_frame, textvariable=self.prod_name, width=40, bg=TEXT_BG, fg=TEXT_FG)
        self.prodname_entry.pack(side='left', fill='x', expand=True)

        # JSON directory
        json_frame = tk.Frame(left_frame, bg=BG_COLOR)
        json_frame.pack(pady=0, fill='x', expand=True)

        tk.Label(json_frame, text="JSON Preset:", fg=TEXT_FG, bg=BG_COLOR).pack(pady=0, fill='x')
        self.json_entry = tk.Entry(json_frame, textvariable=self.preset_path, width=40, bg=TEXT_BG, fg=TEXT_FG)
        self.json_entry.pack(side='left', fill='x', expand=True)
        
        tk.Button(json_frame, text="Browse", command=self.select_preset_file, bg=BUTTON_COLOR, fg=TEXT_FG).pack(side='left', padx=5)
        
        # Source directory
        tk.Label(left_frame, text="Source Folder (A):", fg=TEXT_FG, bg=BG_COLOR).pack(pady=5, fill='x')
        source_frame = tk.Frame(left_frame, bg=BG_COLOR)
        source_frame.pack(pady=5, fill='x', expand=True)
        
        self.source_entry = tk.Entry(source_frame, textvariable=self.source_path, width=40, bg=TEXT_BG, fg=TEXT_FG)
        self.source_entry.pack(side='left', fill='x', expand=True)
        
        tk.Button(source_frame, text="Browse", command=self.select_source_folder, bg=BUTTON_COLOR, fg=TEXT_FG).pack(side='left', padx=5)

        # Destination directory
        tk.Label(left_frame, text="Destination Folder (B):", fg=TEXT_FG, bg=BG_COLOR).pack(pady=5, fill='x')
        dest_frame = tk.Frame(left_frame, bg=BG_COLOR)
        dest_frame.pack(pady=5, fill='x', expand=True)
        
        self.dest_entry = tk.Entry(dest_frame, textvariable=self.dest_path, width=40, bg=TEXT_BG, fg=TEXT_FG)
        self.dest_entry.pack(side='left', fill='x', expand=True)
        
        tk.Button(dest_frame, text="Browse", command=self.select_dest_folder, bg=BUTTON_COLOR, fg=TEXT_FG).pack(side='left', padx=5)

        # Exclusion options
        tk.Label(left_frame, text="Exclude Sequences or Shots (comma-separated):", fg=TEXT_FG, bg=BG_COLOR).pack(pady=5, fill='x')
        self.exclude_entry = tk.Entry(left_frame, width=60, bg=TEXT_BG, fg=TEXT_FG)
        self.exclude_entry.pack(pady=5, fill='x', expand=True)

        # Control buttons
        tk.Button(left_frame, text="Preview", command=self.preview_mode, bg=BUTTON_COLOR, fg=TEXT_FG).pack(pady=5, fill='x')
        tk.Button(left_frame, text="Start Copy", command=self.start_copy_thread, bg=BUTTON_COLOR, fg=TEXT_FG).pack(pady=5, fill='x')

        # Log display
        self.createPresetsGrid(self.right_frame)

        self.log_display = ScrolledText(self.right_frame, height=10, width=40, bg=LOG_BG_COLOR, fg=TEXT_FG)
        self.log_display.pack(pady=5, fill='both', expand=True, side="bottom")
        
        # log header
        log_header_frame = tk.Frame(self.right_frame, bg=BG_COLOR)
        log_header_frame.pack(side="bottom", pady=5, fill='x')
        tk.Label(log_header_frame, text="Log:", fg=TEXT_FG, bg=BG_COLOR).pack(pady=5, fill='x', side="left")
        tk.Button(
            log_header_frame,
            command=lambda:self.log_display.delete(1.0, tk.END),
            text="Clear",
            fg=TEXT_FG,
            bg=BUTTON_COLOR
            ).pack(pady=5, fill='x', side="right")
        

        # Progress bars (outside left-right separation)
        progress_frame = tk.Frame(root, bg=BG_COLOR)  # Set the background of the progress frame
        progress_frame.pack(side='bottom', fill='x', padx=10, pady=10)

        tk.Label(progress_frame, text="Overall Progress:", fg=TEXT_FG, bg=BG_COLOR).pack(pady=5, fill='x')
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, style="TProgressbar")
        self.progress_bar.pack(pady=5, fill='x', expand=True)

        tk.Label(progress_frame, text="File Copy Progress:", fg=TEXT_FG, bg=BG_COLOR).pack(pady=5, fill='x')
        self.indiv_progress_var = tk.DoubleVar()
        self.indiv_progress_bar = ttk.Progressbar(progress_frame, variable=self.indiv_progress_var, maximum=100, style="TProgressbar")
        self.indiv_progress_bar.pack(pady=5, fill='x', expand=True)

        # Styling the progress bars
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", thickness=20, troughcolor=PROGRESS_BG, background=PROGRESS_FG)

        self.load_saved_values()

        # Bind the window close event to save config
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)


    def createPresetsGrid(self, frame: tk.Frame, max_width=3):
        glob_pattern = os.path.join(file_utils.JSON_DIRECTORY, "*.json")
        json_paths = glob.glob(glob_pattern)
        json_filters = []
        for json_path in json_paths:
            with open(json_path, "r") as js:
                data: dict = json.load(js)
                # not a redondant check because empty dict are evaluated False
                if data.get(FILTER_KEY, False) == False:
                    continue
                if not data.get(PRODUCTION_KEY, False):
                    filename = os.path.basename(json_path)
                    data[PRODUCTION_KEY] = os.path.splitext(filename)[0] 
                json_filters.append([json_path, data])

        self.header_frame = tk.Frame(frame, bg=BG_COLOR)
        self.header_frame.pack(fill='x', expand=False)
        self.preset_frame = tk.Frame(frame, bg=BG_COLOR)
        self.preset_frame.pack(fill='x', expand=False)
        
        tk.Label(self.header_frame, text="Presets:", fg=TEXT_FG, bg=BG_COLOR).pack(pady=5, fill='x', side="left")
        refresh_button = tk.Button(
            self.header_frame,
            command=self.refresh,
            text="Refresh",
            fg=TEXT_FG,
            bg=BUTTON_COLOR)
        refresh_button.pack(side="right")

        for i, data in enumerate(json_filters):
            json_path, json_data = data
            production_name = json_data.get(PRODUCTION_KEY, False)
            if json_data.get(PRODUCTION_KEY, False) == False:
                continue
            
            button = tk.Button(
                self.preset_frame,
                text=production_name,
                command=lambda path=json_path: self.load_preset(path),
                bg=BUTTON_COLOR,
                fg=TEXT_FG,
                width=20
            )
            button.grid(sticky="nsew", column=i%max_width, row=i//max_width)
            
        for col in range(self.preset_frame.grid_size()[0]):
            self.preset_frame.columnconfigure(col, weight=1)
        for row in range(self.preset_frame.grid_size()[1]):
            self.preset_frame.rowconfigure(row, weight=1)

    def refresh(self):
        self.preset_frame.pack_forget()
        self.header_frame.pack_forget()
        self.createPresetsGrid(self.right_frame)
        self.log("Presets refreshed")

    def update_overall_progress(self, progress):
        """ Met à jour la barre de progression globale """
        self.progress_var.set(progress)
        self.progress_bar.update()

    def update_file_progress(self, progress):
        """ Met à jour la barre de progression d'un fichier ou d'une séquence d'images """
        self.indiv_progress_var.set(progress)
        self.indiv_progress_bar.update()    

    def select_preset_file(self):
        filename = filedialog.askopenfilename(initialdir=file_utils.JSON_DIRECTORY)
        if filename:
            self.load_preset(filename)
            
    def load_preset(self, filename: str):
        self.preset_path.set(filename)
        self.department_identifiers = file_utils.load_or_create_department_identifiers(filename)
        self.load_json_content()
            
    def select_source_folder(self):
        folder = filedialog.askdirectory(initialdir="I:/")
        if folder:
            self.source_path.set(folder)

    def select_dest_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_path.set(folder)

    def load_json_content(self):
        # Load the JSON content into the text widget
        json_str = json.dumps(self.department_identifiers.get('filters', {}), indent=4)
        self.json_text.delete(1.0, tk.END)  # Clear the text widget
        self.json_text.insert(tk.END, json_str)  # Insert JSON content
        prod_name = self.department_identifiers.get(PRODUCTION_KEY, "")
        source_path = self.department_identifiers.get(SOURCE_KEY, "")
        dest_path = self.department_identifiers.get(DEST_KEY, "")
        self.prod_name.set(prod_name)
        self.source_path.set(source_path)
        self.dest_path.set(dest_path)
            
    def save_json_content(self, to_preset=False):
        # Get the content from the text widget
        new_json_str = self.json_text.get(1.0, tk.END).strip()
        
        try:
            # Parse the new JSON content
            new_data = json.loads(new_json_str)
            
            self.department_identifiers[PRODUCTION_KEY] = self.prod_name.get()
            self.department_identifiers[SOURCE_KEY] = self.source_path.get()
            self.department_identifiers[DEST_KEY] = self.dest_path.get()
            self.department_identifiers[FILTER_KEY] = new_data
            
            # Save it to the JSON file
            try:
                if to_preset and self.preset_path.get():
                    with open(self.preset_path.get(), mode='w') as f:
                        json.dump(self.department_identifiers, f, indent=4)
                else:
                    with filedialog.asksaveasfile(defaultextension=".json") as f:
                        json.dump(self.department_identifiers, f, indent=4)
            except:
                self.log("Save cancelled")
                return

            # Log success
            self.log("JSON file saved.")

            self.refresh()
        except json.JSONDecodeError as e:
            self.log(f"Error updating JSON file: {e}")

    def log(self, message):
        self.log_display.insert(tk.END, message + "\n")
        self.log_display.see(tk.END)
        
    def load_saved_values(self):
        if 'source' in self.config:
            self.source_path.set(self.config['source'])
        if 'destination' in self.config:
            self.dest_path.set(self.config['destination'])

    def preview_mode(self):
        self.log("Preview mode is running...")

        project_directory = self.source_path.get()  # From the Tkinter entry field
        # Clean and filter exclusions: remove empty strings or spaces
        exclusions = [ex.strip() for ex in self.exclude_entry.get().split(",") if ex.strip()]

        # Load the department and identifier data from the JSON file (already loaded in __init__)
        department_identifiers = self.department_identifiers.get(FILTER_KEY, {})

        # Find the Shots directory inside 03_Production
        shots_directory = file_utils.find_shots_directory(project_directory, log_func=self.log)

        if shots_directory:
            self.log(f"Found Shots directory: {shots_directory}")
            self.log("Please wait...")
            # Call find_files using the loaded department identifiers and exclusions
            found_files = file_utils.find_files(shots_directory, department_identifiers, exclusions, log_func=self.log)

            # Log the found files
            for base_name, info in found_files.items():
                self.log(f"File: {base_name}, Version: {info['version']}, Departement: {info['departement']}, Identifier: {info['identifier']}")
        else:
            self.log("Error: 'Shots' directory not found in '03_Production'.")

    def start_copy_thread(self):
        """ Start the file copy operation in a separate thread. """
        copy_thread = threading.Thread(target=self.start_copy_mode)
        copy_thread.start()

    def start_copy_mode(self):
        self.log("Copy mode is running...")

        project_directory = self.source_path.get()  # From the Tkinter entry field
        dest_directory = self.dest_path.get()  # Destination folder
        # Clean and filter exclusions: remove empty strings or spaces
        exclusions = [ex.strip() for ex in self.exclude_entry.get().split(",") if ex.strip()]

        # Find the Shots directory inside 03_Production
        shots_directory = file_utils.find_shots_directory(project_directory, log_func=self.log)

        if shots_directory:
            self.log(f"Found Shots directory: {shots_directory}")
            self.log("Please wait...")
            # Load the department and identifier data from the JSON file (already loaded in __init__)
            department_identifiers = self.department_identifiers.get(FILTER_KEY, {})

            # Call find_files to find the source files with exclusions
            found_files = file_utils.find_files(shots_directory, department_identifiers, exclusions, log_func=self.log)
            # Call copy_files to copy from source to destination, and rename the files
            file_utils.copy_files(found_files, dest_directory, log_func=self.log, 
                       update_overall_progress=self.update_overall_progress,
                       update_file_progress=self.update_file_progress)
        else:
            self.log("Error: 'Shots' directory not found in '03_Production'.")

        self.log("--------------------")
        self.log("------ Done ! ------")
        self.log("--------------------")


    def on_closing(self):
        # Save the config and JSON before closing
        self.config['source'] = self.source_path.get()
        self.config['destination'] = self.dest_path.get()

        save_config(self.config)

        # Save the department identifiers JSON
        preset_path = self.preset_path.get()
        if not preset_path:
            preset_path = file_utils.json_default_name
        file_utils.save_department_identifiers(self.department_identifiers, preset_path)

        self.root.destroy()


# Tkinter main loop
def main():
    root = tk.Tk()
    app = CopyApp(root)
    root.mainloop()
    
if __name__ == '__main__':
    main()