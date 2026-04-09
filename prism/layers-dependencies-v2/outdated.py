from pathlib import Path
from src.core import get_status_tree
import gazu
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
PROJECTS = os.getenv('PROJECTS', '')
PROJECTS = [p.strip() for p in PROJECTS.split(',') if p.strip()]

KITSU_API_URL = "https://illogic-studios.cg-wire.com/api"
DEPARTMENTS = {
    "_layer_lgt_master": "Lighting",
    "_layer_anm_master": "Anim",
    "_layer_cfx_master": "CFX",
    "_layer_fx_master": "FX",
    "_layer_lay_master": "Layout"
}

def update_kitsu_shot_tag(proj_name, seq_name, shot_name, layers_to_update):
    """
    Met à jour le tag du shot dans Kitsu via gazu pour y inscrire les layers à mettre à jour.
    Si aucun layer n'est outdated, on vide la case 'to_update'.
    """
    project = gazu.project.get_project_by_name(proj_name)
    if not project:
        print(f"Projet '{proj_name}' non trouvé dans Kitsu.")
        return
    
    sequence = gazu.shot.get_sequence_by_name(project, seq_name)
    if not sequence:
        print(f"Sequence '{seq_name}' non trouvée dans le projet '{proj_name}'.")
        return

    shot = gazu.shot.get_shot_by_name(sequence, shot_name)
    if not shot:
        print(f"Shot '{shot_name}' non trouvé dans le projet '{proj_name}'.")
        return
        
    data = shot.get("data") or {}

    if layers_to_update:
        data["to_update"] = ', '.join(layers_to_update)
    else:
        if "to_update" in data:
            data["to_update"] = ''

    shot["data"] = data
    gazu.shot.update_shot(shot)

if __name__ == "__main__":
    gazu.set_host(KITSU_API_URL)
    gazu.set_token(ACCESS_TOKEN)

    for proj_name in PROJECTS:
        root_path = Path("I://") / proj_name / "03_Production" / "Shots"
        # root_path = Path("R:\pipeline\pipe_public\prism-playground\prism_playground") / "03_Production" / "Shots"
        tree = get_status_tree(root_path)
        for seq_name, shots in tree.items():
            for shot_name, layers in shots.items():
                outdated_layers = {layer_name: info for layer_name, info in layers.items() if info.get("status") == "outdated"}
                update_kitsu_shot_tag(proj_name, seq_name, shot_name, list(outdated_layers.keys()))