import os
import ast
import json

# --- 1. The Parser ---
def get_file_summary(filepath):
    """Parses a python file to extract high-level structure."""
    content = ""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            tree = ast.parse(content)
    except SyntaxError:
        lines = content.split('\n')[:10]
        return {
            "error": "Syntax Error (Likely Python 2)",
            "preview": [l.strip() for l in lines if l.strip()]
        }
    except Exception as e:
        return {"error": str(e)}

    summary = {
        "docstring": ast.get_docstring(tree) or "No docstring",
        "imports": [],
        "functions": [],
        "classes": []
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                summary["imports"].append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                summary["imports"].append(node.module)
        elif isinstance(node, ast.FunctionDef):
            if node.name != "__init__": 
                summary["functions"].append(node.name)
        elif isinstance(node, ast.ClassDef):
            summary["classes"].append(node.name)

    summary["imports"] = list(set(summary["imports"]))[:8]
    summary["docstring"] = summary["docstring"].split('\n')[0][:150]
    
    return summary

# --- 2. The Scanner Logic ---
def scan_folder_recursively(start_path, root_context):
    local_map = {}
    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')] 
        
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_context)
                
                print(f"    Scanning: {file}") 
                local_map[rel_path] = get_file_summary(full_path)
    return local_map

def main_split_scan(root_dir, output_dir):
    root_dir = os.path.abspath(root_dir)
    output_dir = os.path.abspath(output_dir)

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    print(f"Starting SPLIT scan of: {root_dir}")
    print(f"Output logs to: {output_dir}")
    print("=" * 60)

    try:
        items = os.listdir(root_dir)
    except FileNotFoundError:
        print(f"Error: Directory {root_dir} not found.")
        return

    subdirs = [d for d in items if os.path.isdir(os.path.join(root_dir, d)) and not d.startswith('.')]
    root_files = [f for f in items if os.path.isfile(os.path.join(root_dir, f)) and f.endswith('.py')]

    # 1. Process Root Files
    if root_files:
        print(f"[Root Folder] Processing files...")
        root_map = {}
        for f in root_files:
            full_path = os.path.join(root_dir, f)
            print(f"    Scanning: {f}")
            root_map[f] = get_file_summary(full_path)
        
        outfile = os.path.join(output_dir, "pipeline_map_root.json")
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump(root_map, f, indent=2)
        print(f">> SAVED: {outfile}\n")

    # 2. Process Subdirectories
    for folder in subdirs:
        print(f"[{folder.upper()}] Processing folder...")
        folder_path = os.path.join(root_dir, folder)
        
        folder_data = scan_folder_recursively(folder_path, root_dir)
        
        if folder_data:
            outfile = os.path.join(output_dir, f"pipeline_map_{folder}.json")
            with open(outfile, 'w', encoding='utf-8') as f:
                json.dump(folder_data, f, indent=2)
            print(f">> SAVED: {outfile}\n")
        else:
            print(f">> Skipped (No Python files found).\n")

if __name__ == "__main__":
    # --- CONFIGURATION ---
    scan_root = "R:/pipeline/pipe"    # Where to read from
    json_output_dir = "C:/out_scan/"  # Where to save JSONs
    
    main_split_scan(scan_root, json_output_dir)
    print("All scans complete.")