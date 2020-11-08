
import os
import pprint
os.sys.path.append("D:\gazu")
import gazu

#Connection
gazu.client.set_host("https://bloom.cg-wire.com/api")
gazu.log_in("gabriel@bloompictures.tv", "cgwirebloom")

#Get project ID
project = gazu.project.get_project_by_name("Maestro")
project_id = project["id"]

#Get Output type dic (Geo)
output_types = gazu.files.all_output_types()
output_type_dict = output_types[0]

#Get person
person = gazu.person.get_person_by_full_name("Gabriel Grapperon")

#Get Software dic
softwares = gazu.files.all_softwares()
software_dict = gazu.files.get_software_by_name("Maya")

#Get Asset
asset_dic = gazu.asset.get_asset_by_name(project, "toto")

#Get Task dic
modelinq =gazu.task.get_task_type_by_name("Modeling") #task type
task_dict = gazu.task.get_task_by_name(asset_dic, modelinq)


#Create a new working file
"""
working_file = gazu.files.new_working_file(
    task_dict,
    name="main",
    software=software_dict,
    comment="super comment",
    person=None, # Automatically set as current user if set to None
    revision=0, # If revision == 0, it is set as latest revision + 1
    sep="/"
)
working_files = gazu.files.get_working_files_for_task(task_dict)
pp = pprint.PrettyPrinter(width=41)
pp.pprint(working_files)
"""

#Update project file tree
gazu.files.update_project_file_tree(project_id,
{
    "working": {
        "mountpoint": "",
        "root": "projects",
        "folder_path": {
            "asset": "<Project>/lib/<AssetType>",
            "shot": "<Project>/scenes/<Sequence>/<Shot>",
            "sequence": "<Project>/sequences/<Sequence>/<TaskType>",
            "scene": "<Project>/scenes/<Sequence>/<Scene>/<TaskType>",
            "style": "lowercase"
        },
        "file_name": {
            "asset": "<Asset>",
            "shot": "<Sequence>_<Shot>",
            "sequence": "<Sequence>",
            "scene": "<Scene>",
            "style": "lowercase"
        }
    },
    "output": {
        "mountpoint": "/simple",
        "root": "productions/export",
        "folder_path": {
            "shot": "<Project>/shots/<Sequence>/<Shot>/<OutputType>",
            "asset": "<Project>/assets/<AssetType>/<Asset>/<OutputType>",
            "sequence": "<Project>/sequences/<Sequence>/<OutputType>",
            "scene": "<Project>/scenes/<Sequence>/<Scene>/<OutputType>",
            "style": "lowercase"
        },
        "file_name": {
            "shot": "<Project>_<Sequence>_<Shot>_<OutputType>_<OutputFile>",
            "asset": "<Project>_<AssetType>_<Asset>_<OutputType>_<OutputFile>",
            "sequence": "<Project>_<Sequence>_<OuputType>_<OutputFile>",
            "scene": "<Project>_<Sequence>_<Scene>_<OutputType>_<OutputFile>",
            "style": "lowercase"
        }
    },
    "preview": {
        "mountpoint": "/simple",
        "root": "productions/previews",
        "folder_path": {
            "shot": "<Project>/shots/<Sequence>/<Shot>/<TaskType>",
            "asset": "<Project>/assets/<AssetType>/<Asset>/<TaskType>",
            "sequence": "<Project>/sequences/<Sequence>/<TaskType>",
            "scene": "<Project>/scene/<Scene>/<TaskType>",
            "style": "lowercase"
        },
        "file_name": {
            "shot": "<Project>_<Sequence>_<Shot>_<TaskType>",
            "asset": "<Project>_<AssetType>_<Asset>_<TaskType>",
            "sequence": "<Project>_<Sequence>_<TaskType>",
            "scene": "<Project>_<Scene>_<TaskType>",
            "style": "lowercase"
        }
    }
}
)

#Get last working file
working_files = gazu.files.get_last_working_files(task_dict)
#pp = pprint.PrettyPrinter(width=41)
#pp.pprint(working_files['main']["id"])

#Build path for last working file
file_path = gazu.files.build_working_file_path(
    task_dict,
    name="main",
    software=software_dict,
    revision =1,
    sep="/"
)
print "Working file path:" + file_path

#Create new output file
output_file = gazu.files.new_entity_output_file(
    entity = asset_dic["id"], # or shot_dict
    output_type = output_type_dict["id"],
    task_type = modelinq["id"],
    comment = "comment",
    working_file = working_files['main']["id"],
    person=person["id"], # author
    revision=0,
    name='main',
    mode='output',
    nb_elements=1, # change it only for image sequences
    representation="mb",
    sep="/",
    file_status_id=None

)

output_files_dict = gazu.files.get_last_output_files_for_entity(asset_dic)
output_files = gazu.files.all_output_files_for_entity(asset_dic, output_type_dict, representation="mb")
pp = pprint.PrettyPrinter(width=41)
pp.pprint(output_files_dict)
filepath =  output_files_dict[0]["path"]+"_"+str(output_files_dict[0]["revision"])+output_files_dict[0]["representation"]
print filepath
