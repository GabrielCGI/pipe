import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
import json

import file_utils


# Path for the configuration file
JSON_DIRECTORY = os.path.join(os.path.expanduser("~"), "Documents", "CopyApp")
JSON_DIRECTORY = "R:/pipeline/pipe/windows/CopyMediaPrism/configs"
config_file_path = "copy_config.json"

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
    def __init__(self, root):
        self.root = root
        self.root.title("Media Copy Tool")
        self.root.geometry("1500x1000")
        
        self.preset_path = tk.StringVar()
        self.source_path = tk.StringVar()
        self.dest_path = tk.StringVar()
        
        # Load or create department identifiers JSON
        self.config = load_config()  # Load saved configuration
        preset_file = self.config.get("preset", file_utils.json_default_name)
        self.department_identifiers = file_utils.load_or_create_department_identifiers(preset_file)

        # Color configuration
        bg_color = '#475C7A'        # Background color
        button_color = '#685D79'    # Button color
        log_bg_color = '#685D79'    # Log background color
        progress_bg = '#685D79'     # Progress bar background
        progress_fg = '#D8737F'     # Progress bar progress color
        text_bg = '#AB6C82'         # Text field background color
        text_fg = '#FCBB6D'         # Text color

        # Main layout
        self.main_frame = tk.Frame(root, bg=bg_color)
        self.main_frame.pack(fill='both', expand=True)

        # Left side: Source, destination, exclusions, JSON editor, buttons
        left_frame = tk.Frame(self.main_frame, bg=bg_color)
        left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

        # Right side: Log area
        right_frame = tk.Frame(self.main_frame, bg=bg_color)
        right_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # Frame for the JSON editor (taking half of the left column)
        json_frame = tk.Frame(left_frame, bg=bg_color)
        json_frame.pack(pady=5, fill='x', expand=False)  # Not expanding to limit height

        tk.Label(json_frame, text="Department Identifiers (JSON):", fg=text_fg, bg=bg_color).pack(pady=5, fill='x')

        # Scrollable Text widget for displaying and editing the JSON content
        self.json_text = ScrolledText(json_frame, bg=text_bg, fg=text_fg) # self.json_text = ScrolledText(json_frame, height=10, bg=text_bg, fg=text_fg)
        self.json_text.pack(pady=5, fill='x', expand=True)

        # Load the current JSON content into the text widget
        self.load_json_content()

        # Button to save the modified JSON
        json_save_buttons = tk.Frame(json_frame, bg=bg_color)
        json_save_buttons.pack(pady=5, fill='x', expand=False)

        tk.Button(json_save_buttons, text="Save", command=self.save_to_preset_json, bg=button_color, fg=text_fg).pack(pady=5, fill='x')
        tk.Button(json_save_buttons, text="Save as new JSON", command=self.save_json_content, bg=button_color, fg=text_fg).pack(pady=5, fill='x')

        # JSON directory
        json_frame = tk.Frame(left_frame, bg=bg_color)
        json_frame.pack(pady=0, fill='x', expand=True)

        tk.Label(json_frame, text="JSON Preset:", fg=text_fg, bg=bg_color).pack(pady=0, fill='x')
        self.json_enty = tk.Entry(json_frame, textvariable=self.preset_path, width=40, bg=text_bg, fg=text_fg)
        self.json_enty.pack(side='left', fill='x', expand=True)
        
        tk.Button(json_frame, text="Browse", command=self.select_preset_file, bg=button_color, fg=text_fg).pack(side='left', padx=5)
        
        # Source directory
        tk.Label(left_frame, text="Source Folder (A):", fg=text_fg, bg=bg_color).pack(pady=5, fill='x')
        source_frame = tk.Frame(left_frame, bg=bg_color)
        source_frame.pack(pady=5, fill='x', expand=True)
        
        self.source_entry = tk.Entry(source_frame, textvariable=self.source_path, width=40, bg=text_bg, fg=text_fg)
        self.source_entry.pack(side='left', fill='x', expand=True)
        
        tk.Button(source_frame, text="Browse", command=self.select_source_folder, bg=button_color, fg=text_fg).pack(side='left', padx=5)

        # Destination directory
        tk.Label(left_frame, text="Destination Folder (B):", fg=text_fg, bg=bg_color).pack(pady=5, fill='x')
        dest_frame = tk.Frame(left_frame, bg=bg_color)
        dest_frame.pack(pady=5, fill='x', expand=True)
        
        self.dest_entry = tk.Entry(dest_frame, textvariable=self.dest_path, width=40, bg=text_bg, fg=text_fg)
        self.dest_entry.pack(side='left', fill='x', expand=True)
        
        tk.Button(dest_frame, text="Browse", command=self.select_dest_folder, bg=button_color, fg=text_fg).pack(side='left', padx=5)

        # Exclusion options
        tk.Label(left_frame, text="Exclude Sequences or Shots (comma-separated):", fg=text_fg, bg=bg_color).pack(pady=5, fill='x')
        self.exclude_entry = tk.Entry(left_frame, width=60, bg=text_bg, fg=text_fg)
        self.exclude_entry.pack(pady=5, fill='x', expand=True)

        # Control buttons
        tk.Button(left_frame, text="Preview", command=self.preview_mode, bg=button_color, fg=text_fg).pack(pady=5, fill='x')
        tk.Button(left_frame, text="Start Copy", command=self.start_copy_thread, bg=button_color, fg=text_fg).pack(pady=5, fill='x')

        # Log display
        tk.Label(right_frame, text="Log:", fg=text_fg, bg=bg_color).pack(pady=5, fill='x')
        self.log_display = ScrolledText(right_frame, height=10, width=40, bg=log_bg_color, fg=text_fg)
        self.log_display.pack(pady=5, fill='both', expand=True)

        # Progress bars (outside left-right separation)
        progress_frame = tk.Frame(root, bg=bg_color)  # Set the background of the progress frame
        progress_frame.pack(side='bottom', fill='x', padx=10, pady=10)

        tk.Label(progress_frame, text="Overall Progress:", fg=text_fg, bg=bg_color).pack(pady=5, fill='x')
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100, style="TProgressbar")
        self.progress_bar.pack(pady=5, fill='x', expand=True)

        tk.Label(progress_frame, text="File Copy Progress:", fg=text_fg, bg=bg_color).pack(pady=5, fill='x')
        self.indiv_progress_var = tk.DoubleVar()
        self.indiv_progress_bar = ttk.Progressbar(progress_frame, variable=self.indiv_progress_var, maximum=100, style="TProgressbar")
        self.indiv_progress_bar.pack(pady=5, fill='x', expand=True)

        # Styling the progress bars
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TProgressbar", thickness=20, troughcolor=progress_bg, background=progress_fg)

        self.load_saved_values()

        # Bind the window close event to save config
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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
        source_path = self.department_identifiers.get("source_path", "")
        dest_path = self.department_identifiers.get("dest_path", "")
        self.source_path.set(source_path)
        self.dest_path.set(dest_path)

    def save_to_preset_json(self):
        # Get the content from the text widget
        if not self.preset_path.get():
            self.save_json_content()
            
        new_json_str = self.json_text.get(1.0, tk.END).strip()
        try:
            # Parse the new JSON content
            new_data = json.loads(new_json_str)
            
            self.department_identifiers["filters"] = new_data
            self.department_identifiers["source_path"] = self.source_path.get()
            self.department_identifiers["dest_path"] = self.dest_path.get()
            
            # Save it to the JSON file
            try:
                with open(self.preset_path.get(), mode='w') as f:
                    json.dump(self.department_identifiers, f, indent=4)
            except:
                self.log("Save cancelled")
                return

            # Log success
            self.log("JSON file saved.")

        except json.JSONDecodeError as e:
            self.log(f"Error updating JSON file: {e}")
            
            
    def save_json_content(self):
        # Get the content from the text widget
        new_json_str = self.json_text.get(1.0, tk.END).strip()
        
        try:
            # Parse the new JSON content
            new_data = json.loads(new_json_str)
            
            self.department_identifiers["filters"] = new_data
            self.department_identifiers["source_path"] = self.source_path.get()
            self.department_identifiers["dest_path"] = self.dest_path.get()
            
            # Save it to the JSON file
            try:
                with filedialog.asksaveasfile(defaultextension=".json") as f:
                    json.dump(self.department_identifiers, f, indent=4)
            except:
                self.log("Save cancelled")
                return

            # Log success
            self.log("JSON file saved.")

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
        department_identifiers = self.department_identifiers.get('filters', {})

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
            department_identifiers = self.department_identifiers.get('filters', {})

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