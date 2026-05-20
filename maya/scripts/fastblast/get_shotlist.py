import os
import sys

MODULE_PATH = os.path.join(
    os.getenv("ILL_PYTHON_SHARE_PATH"),
    "python311_fastblast_pkgs",
    "Lib",
    "site-packages",
)
if MODULE_PATH not in sys.path:
    sys.path.insert(0, MODULE_PATH)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

API_URL = os.getenv("API_URL")
SCRIPT_NAME = os.getenv("SCRIPT_NAME")
API_KEY = os.getenv("API_KEY")

def get_shotgrid_shotlist(sg, project_name):

    # First get the project ID
    projects = sg.find("Project",
                        filters=[["name", "is", project_name]],
                        fields=["id"])
    
    if projects:
        project_ref = projects[0]
        # Now find shots in that sequence
        shots = sg.find("Shot",
                        filters=[["project", "is", project_ref]],
                        fields=["code", "sg_cut_order", "sg_status_list"])
        # print(shots)
        return shots

    return []

def format_shots_with_sequence(shots, sg):
    """
    Takes a list of shot dictionaries and returns an ordered list with sequence info.
    Filters out shots with no cut order.
    Queries ShotGrid to get the actual sequence for each shot.
    
    Args:
        shots: List of shot dictionaries with 'code' and 'sg_cut_order' fields
        sg: ShotGrid API instance
        
    Returns:
        List of shots ordered by cut order, in the format sequence/shot (e.g SQ010-Ballin/SH010)
    """
    # Filter shots with valid cut order
    shots_with_order = [shot for shot in shots if shot.get('sg_cut_order') is not None]
    
    # Sort by cut order
    sorted_shots = sorted(shots_with_order, key=lambda x: x['sg_cut_order'])
    
    # Format with sequence data from ShotGrid
    formatted_shots = []
    for shot in sorted_shots:
        # Get sequence info from ShotGrid
        sequence_data = sg.find_one("Shot",
                                    filters=[["id", "is", shot['id']]],
                                    fields=["sg_sequence"])
        
        sequence = None
        if sequence_data and sequence_data.get('sg_sequence'):
            sequence = sequence_data['sg_sequence']['name']
        
        formatted_shots.append(sequence + "/" + shot['code'])

    
    return formatted_shots

def get_shot_order(project_name):

    try:
        import shotgun_api3 # type: ignore
    except ImportError:
        print("Could not import shotgun API, returning no shot order")
        return []

    sg = None
    shot_order = []
    try:
        sg = shotgun_api3.Shotgun(API_URL, script_name=SCRIPT_NAME, api_key=API_KEY)
    except Exception as e:
        print("Could not connect to shotgrid project", e)
    
    if sg:
        shots = get_shotgrid_shotlist(project_name=project_name, sg=sg)
        shot_order = format_shots_with_sequence(shots=shots, sg=sg)

    if "API_URL" in os.environ:
        del os.environ["API_URL"]
    if "API_KEY" in os.environ:
        del os.environ["API_KEY"]
    if "SCRIPT_NAME" in os.environ:
        del os.environ["SCRIPT_NAME"]

    return shot_order

