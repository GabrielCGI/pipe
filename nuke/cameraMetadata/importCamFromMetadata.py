import nuke
import os

def create_camera_from_exr_metadata():
    """
    Créer une caméra à partir de la metadata 'exr/cameraLayerPath' 
    du node Read sélectionné par l'utilisateur
    """
    
    # Vérifier qu'un node est sélectionné
    selected_nodes = nuke.selectedNodes()
    
    if not selected_nodes:
        nuke.message("Erreur: Aucun node sélectionné. Veuillez sélectionner un node Read.")
        return
    
    if len(selected_nodes) > 1:
        nuke.message("Erreur: Plusieurs nodes sélectionnés. Veuillez sélectionner un seul node Read.")
        return
    
    read_node = selected_nodes[0]
    
    # Vérifier que c'est bien un node Read
    if read_node.Class() != 'Read':
        nuke.message("Erreur: Le node sélectionné n'est pas un node Read. Classe détectée: {}".format(read_node.Class()))
        return
    
    try:
        # Récupérer toutes les métadonnées du node Read
        metadata = read_node.metadata()
        
        if not metadata:
            nuke.message("Erreur: Aucune metadata trouvée dans le node Read sélectionné.")
            return
        
        # Chercher la metadata 'exr/cameraLayerPath'
        camera_path = None
        camera_metadata_key = 'exr/cameraLayerPath'
        
        if camera_metadata_key in metadata:
            camera_path = metadata[camera_metadata_key]
        else:
            # Afficher toutes les clés disponibles pour debug
            available_keys = list(metadata.keys())
            exr_keys = [key for key in available_keys if 'exr' in key.lower() or 'camera' in key.lower()]
            
            error_msg = "Erreur: Metadata '{}' non trouvée.\n\n".format(camera_metadata_key)
            if exr_keys:
                error_msg += "Métadonnées EXR/Camera trouvées:\n{}".format('\n'.join(exr_keys))
            else:
                error_msg += "Aucune metadata EXR/Camera trouvée.\n\nTous les keys disponibles:\n{}".format('\n'.join(available_keys[:20]))
                if len(available_keys) > 20:
                    error_msg += "\n... et {} autres".format(len(available_keys) - 20)
            
            nuke.message(error_msg)
            return
        
        if not camera_path:
            nuke.message("Erreur: La metadata '{}' existe mais est vide.".format(camera_metadata_key))
            return
        
        # Vérifier que le fichier de caméra existe
        if not os.path.exists(camera_path):
            nuke.message("Erreur: Le fichier de caméra spécifié n'existe pas:\n{}".format(camera_path))
            return
        
        # Créer le node Camera3
        camera_node = nuke.createNode('Camera3')
        
        # Définir le fichier de la caméra
        camera_path_corrected = camera_path.replace('\\', '/')
        camera_node['file'].setValue(camera_path_corrected)
        camera_node['read_from_file'].setValue(1)
        
        # Positionner la caméra près du node Read
        read_x = read_node['xpos'].value()
        read_y = read_node['ypos'].value()
        
        camera_node['xpos'].setValue(read_x + 200)
        camera_node['ypos'].setValue(read_y)
        
        # Renommer la caméra avec un nom descriptif
        base_name = os.path.splitext(os.path.basename(camera_path))[0]
        camera_node['name'].setValue("Camera_{}".format(base_name))
        
        nuke.message("Succès: Caméra créée avec le fichier:\n{}".format(camera_path))
        
        print("Camera créée:")
        print("- Node Read source: {}".format(read_node.name()))
        print("- Fichier caméra original: {}".format(camera_path))
        print("- Fichier caméra corrigé: {}".format(camera_path_corrected))
        print("- Node caméra: {}".format(camera_node.name()))
        
    except Exception as e:
        nuke.message("Erreur lors de la création de la caméra:\n{}".format(str(e)))
        print("Erreur détaillée: {}".format(e))

def list_exr_metadata():
    """
    Fonction utilitaire pour lister toutes les métadonnées EXR d'un node Read sélectionné
    """
    selected_nodes = nuke.selectedNodes()
    
    if not selected_nodes or selected_nodes[0].Class() != 'Read':
        nuke.message("Veuillez sélectionner un node Read.")
        return
    
    read_node = selected_nodes[0]
    metadata = read_node.metadata()
    
    if metadata:
        exr_keys = [key for key in metadata.keys() if 'exr' in key.lower()]
        if exr_keys:
            print("\nMétadonnées EXR trouvées dans {}:".format(read_node.name()))
            for key in sorted(exr_keys):
                print("- {}: {}".format(key, metadata[key]))
        else:
            print("Aucune metadata EXR trouvée.")
    else:
        print("Aucune metadata trouvée.")

# Permet de call depuis init.py/menu.py
def main():
    create_camera_from_exr_metadata()

# Lancer le script principal
if __name__ == "__main__":
    create_camera_from_exr_metadata()

# Pour utiliser la fonction de debug, décommentez la ligne suivante:
# list_exr_metadata()