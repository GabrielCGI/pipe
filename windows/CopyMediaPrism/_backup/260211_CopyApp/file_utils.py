import os
import re
import json
import glob
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
import time
import concurrent.futures

debug = False

# Path to store the JSON in the user's preferences
JSON_DIRECTORY = os.path.join(os.path.expanduser("~"), "Documents", "CopyApp")
# JSON_DIRECTORY = "C:/Users/m.beldjilali/Documents/copyappdev/presets"
JSON_DIRECTORY = "R:/pipeline/pipe/windows/CopyMediaPrism/presets"
json_default_name = os.path.join(JSON_DIRECTORY, "department_identifiers.json")

# Default content for the JSON file
default_identifiers = {
    "COMPOSITING": ["compo", "comp", "nuke","beauty"],
    "ANIM": ["anim", "anim_playblast"],
    "RLO": ["RoughtLayout", "Previz", "RoughLayout_playblast"]
}
added_seq_log_end = []

# Function to create or load the department identifier JSON file
def load_or_create_department_identifiers(json_path=json_default_name):
    os.makedirs(os.path.dirname(JSON_DIRECTORY), exist_ok=True)
    # Check if the directory exists, create it if it doesn't
    documents_dir = os.path.dirname(json_path)
    if not os.path.exists(documents_dir):
        os.makedirs(documents_dir)

    # Create or load the JSON file
    if not os.path.exists(json_path):
        with open(json_path, 'w') as f:
            json.dump(default_identifiers, f, indent=4)
        return default_identifiers
    else:
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If the JSON file is corrupted, reset to default
            with open(json_path, 'w') as f:
                json.dump(default_identifiers, f, indent=4)
            return default_identifiers


# Function to save modified department identifiers
def save_department_identifiers(data, json_path=json_default_name):
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=4)

# Function to locate the "Shots" folder inside "03_Production"
def find_shots_directory(project_dir, log_func=None):
    # Check if "03_Production" exists at the root of the given directory
    production_dir = os.path.join(project_dir, "03_Production")
    shots_dir = os.path.join(production_dir, "Shots")

    # Verify that both "03_Production" and "Shots" exist
    if os.path.exists(production_dir) and os.path.exists(shots_dir):
        return shots_dir
    else:
        if log_func:
            log_func(f"'Shots' directory not found in '03_Production' at {production_dir}")
        return None

# Function to find all media files based on department identifiers, keeping only the highest version for each identifier

def find_files(source_dir, department_identifiers, exclusions=None, log_func=None):
    if exclusions is None:
        exclusions = []  # Default to an empty list if no exclusions are provided

    exclusions.append("_thumbs")

    files_dict = {}
    # Regular expression to find version numbers like _v001
    pattern_version = re.compile(r'_v(\d+)')

    playblast_pattern = source_dir + "/*/*/Playblasts/**"
    renders2d_pattern = source_dir + "/*/*/Renders/2dRender/**"
    renders3d_pattern = source_dir + "/*/*/Renders/3dRender/**"
    
    paths1 = glob.glob(playblast_pattern)
    paths2 = glob.glob(renders2d_pattern)
    paths3 = glob.glob(renders3d_pattern)
    paths = paths1 + paths2 + paths3

    for id_path in paths:

        # Check for excluded sequences or shots, only if exclusions are not empty
        if exclusions and any(exclusion in id_path for exclusion in exclusions):
            if log_func and debug is True:
                log_func(f"Skipping excluded path: {id_path}")
            continue
        
        id_path = Path(id_path)
        if "Playblasts" in id_path.as_posix() and len(id_path.parts) > 7:
            seq_name = id_path.parts[4]
            plan_name = id_path.parts[5]
            identifier = id_path.parts[7].lower()  
        elif "Renders" in id_path.as_posix() and len(id_path.parts) > 8:
            seq_name = id_path.parts[4]
            plan_name = id_path.parts[5]
            identifier = id_path.parts[8].lower()
        else:
            continue


        # For each department, check if the identifier (lowercased) is in the list of identifiers (also lowercased)
        for departement, identifiers in department_identifiers.items():
            if identifier in [i.lower() for i in identifiers]:
                # Look for version numbers in the filename
                
                versions = [v_path for v_path in  id_path.glob("*")]
                versions.sort(reverse=True)
                if versions:
                    found = False
                    for version in versions:
                        if found:
                            break
                        if version.as_posix().endswith(")"):
                            continue
                        
                        for v_path in version.glob("*"):
                            match = pattern_version.search(v_path.as_posix())
                            if match:
                                version = int(match.group(1))
                                base_name = f"{seq_name}_{plan_name}_{departement}"

                                # Keep only the highest version for each identifier in the department
                                if base_name not in files_dict or version > files_dict[base_name]['version']:
                                    files_dict[base_name] = {
                                        'path': v_path.as_posix(),
                                        'version': version,
                                        'departement': departement,
                                        'identifier': identifier,
                                        'sequence': seq_name,
                                        'plan': plan_name,
                                    }
                                    found = True

    if log_func and debug is True:
        for base_name, info in files_dict.items():
            log_func(f"Found file: {base_name}, version: {info['version']}, departement: {info['departement']}")

    return files_dict

# Function to calculate the MD5 checksum of a file
def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Fonction MD5 optimisée pour les fichiers de grande taille (hash partiel)
def calculate_md5_fast(file_path, chunk_size=8192):
    hash_md5 = hashlib.md5()
    total_size = os.path.getsize(file_path)

    with open(file_path, "rb") as f:
        # Lire les premiers et derniers morceaux du fichier pour un hash plus rapide
        start_chunk = f.read(chunk_size)
        f.seek(max(total_size - chunk_size, 0))  # Aller à la fin du fichier
        end_chunk = f.read(chunk_size)

        # Mettre à jour le hash avec les deux morceaux
        hash_md5.update(start_chunk)
        hash_md5.update(end_chunk)

    return hash_md5.hexdigest()

# Utilisation de multithreading pour comparer les fichiers dans une séquence
def compare_md5_in_parallel(files, directory, log_func=None):
    def compare_single_file(file_to_compare):
        full_file_path = os.path.join(directory, file_to_compare)
        return calculate_md5_fast(full_file_path)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Calculer les MD5 en parallèle
        md5_results = list(executor.map(compare_single_file, files))

    return md5_results

def verify_image_sequence_integrity(files_to_copy, log_func=None):
    """
    Vérifie si la séquence d'images est complète (sans frames manquantes).
    """
    frame_numbers = []
    for file_name in files_to_copy:
        match = re.search(r'(\d+)\.(\w+)$', file_name)  # Extraire le numéro de frame
        if match:
            frame_numbers.append(int(match.group(1)))

    # Trier les numéros de frames pour détecter les manquants
    frame_numbers.sort()
    missing_frames = []
    
    if frame_numbers:
        # Vérifier les frames manquantes
        for i in range(frame_numbers[0], frame_numbers[-1]):
            if i not in frame_numbers:
                missing_frames.append(i)

    # Log et retour
    if missing_frames:
        missing_message = f"! Frames manquantes dans la séquence : {missing_frames}"
        if log_func and debug is True:
            log_func(missing_message)
        return missing_frames
    else:
        return None

def delete_image_sequence(image_sequence_folder, log_func=None):
    """
    Supprime le dossier de séquence d'images.
    """
    if os.path.exists(image_sequence_folder):
        shutil.rmtree(image_sequence_folder)
        if log_func and debug is True:
            log_func(f"- Supprimé : séquence d'images {image_sequence_folder}")
    else:
        pass

def delete_video_file(video_file_path, log_func=None):
    """
    Supprime le fichier vidéo (MP4/MOV) s'il existe.
    """
    if os.path.exists(video_file_path):
        os.remove(video_file_path)
        if log_func and debug is True:
            log_func(f"- Supprimé : vidéo {video_file_path}")
    else:
        pass

def copy_files(source_files, dest_dir, log_func=None, enable_md5=True, update_overall_progress=None, update_file_progress=None):
    
    total_files = len(source_files)
    files_copied = 0

    for base_name, info in source_files.items():
        source_file = info['path']
        seq_name = info['sequence']
        plan_name = info['plan']
        departement = info['departement']
        extension = os.path.splitext(source_file)[1].lower()

        if update_file_progress:
            update_file_progress(0)

        sequence_folder = os.path.join(dest_dir, seq_name)
        os.makedirs(sequence_folder, exist_ok=True)

        log_file_path = os.path.join(sequence_folder, f"{seq_name}.log")

        if extension in ['.mp4', '.mov']:
            new_filename = f"{seq_name}_{plan_name}_{departement}{extension}"
            dest_file = os.path.join(sequence_folder, new_filename)
            
            if os.path.exists(dest_file):
                source_md5 = calculate_md5_fast(source_file)
                dest_md5 = calculate_md5_fast(dest_file)
                if source_md5 == dest_md5:
                    log_func(f"[] Skipped (identical): {new_filename}")
                    files_copied += 1
                    if update_overall_progress:
                        update_overall_progress((files_copied / total_files) * 100)
                    continue

            image_sequence_folder = os.path.join(sequence_folder, f"{seq_name}_{plan_name}_{departement}")
            delete_image_sequence(image_sequence_folder, log_func)

            files_to_copy = [source_file]

            for i in range(101):
                if update_file_progress:
                    update_file_progress(i)
                time.sleep(0.001)

            shutil.copy2(source_file, dest_file)
            file_log = f"+ Updated: {new_filename} \n\tfrom {source_file}"
            log_func(file_log)
            with open(log_file_path, 'a') as log_file:
                log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : {file_log}\n")
            files_copied += 1

            if update_overall_progress:
                update_overall_progress((files_copied / total_files) * 100)

        else:
            video_file_mp4 = os.path.join(sequence_folder, f"{seq_name}_{plan_name}_{departement}.mp4")
            video_file_mov = os.path.join(sequence_folder, f"{seq_name}_{plan_name}_{departement}.mov")

            delete_video_file(video_file_mp4, log_func)
            delete_video_file(video_file_mov, log_func)

            image_sequence_folder = os.path.join(sequence_folder, f"{seq_name}_{plan_name}_{departement}")
            os.makedirs(image_sequence_folder, exist_ok=True)

            sequence_base = re.sub(r'(\.\d+)', '', os.path.splitext(os.path.basename(source_file))[0])
            directory = os.path.dirname(source_file)
            files_to_copy = [f for f in os.listdir(directory) if f.startswith(sequence_base) and f.endswith(extension)]

            missing_frames = verify_image_sequence_integrity(files_to_copy, log_func)
            if missing_frames:
                log_func(f"! Frames manquantes dans séquence {seq_name}_{plan_name}_{departement}: {missing_frames}. Copie des fichiers existants uniquement.")
            elif debug is True:
                log_func("Séquence d'images complète")

            if enable_md5:
                # Comparer les fichiers de la séquence avec MD5 en parallèle
                md5_results_source = compare_md5_in_parallel(files_to_copy, directory, log_func)
            else:
                size_list = [os.path.getsize(os.path.join(directory, file)) for file in files_to_copy]
                

            # Variable pour suivre si toute la séquence est identique
            all_skipped = True

            for i, file_to_copy in enumerate(files_to_copy):
                full_file_path = os.path.join(directory, file_to_copy)
                match = re.search(r'(\d+)\.(\w+)$', file_to_copy)
                if match:
                    frame_number = match.group(1)
                    new_filename = f"{seq_name}_{plan_name}_{departement}.{frame_number}{extension}"
                    dest_file = os.path.join(image_sequence_folder, new_filename)
                else:
                    new_filename = f"{seq_name}_{plan_name}_{departement}{extension}"
                    dest_file = os.path.join(image_sequence_folder, new_filename)

                if os.path.exists(dest_file):
                    if enable_md5:
                        source_id = md5_results_source[i]
                        dest_id = calculate_md5_fast(dest_file)
                    else:
                        source_id = size_list[i]
                        dest_id = os.path.getsize(dest_file)
                    if source_id == dest_id:
                        continue  # Passer si les fichiers sont identiques
                    else:
                        all_skipped = False  # Si une image n'est pas identique, on ne skippe pas la séquence entière
                else:
                    all_skipped = False
                shutil.copy2(full_file_path, dest_file)

                if update_file_progress:
                    update_file_progress((i + 1) / len(files_to_copy) * 100)

            if all_skipped:
                log_func(f"[] Skipped (identical): Entire image sequence {seq_name}_{plan_name}_{departement}")
            else:
                log_func(f"+ Updated: Entire image sequence {seq_name}_{plan_name}_{departement}")

            files_copied += 1
            if update_overall_progress:
                overall_progress = (files_copied / total_files) * 100
                update_overall_progress(overall_progress)

            sequence_log = f"+ Updated: {seq_name}_{plan_name}_{departement} \n\tfrom image sequence from {directory}."
            with open(log_file_path, 'a') as log_file:
                log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : {sequence_log}\n")

        if update_file_progress:
            update_file_progress(0)

    # Update end log only
    for base_name, info in source_files.items():
        source_file = info['path']
        seq_name = info['sequence']

        
        #parse seq_name
        if seq_name not in added_seq_log_end:
            sequence_folder = os.path.join(dest_dir, seq_name)
            
            log_file_path = os.path.join(sequence_folder, f"{seq_name}.log")
            with open(log_file_path, 'a') as log_file:
                log_file.write("------------------------------\n")
            added_seq_log_end.append(seq_name)
