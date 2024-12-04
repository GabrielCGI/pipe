import sys
import time
import os

# Ajouter le chemin à votre module DaVinciResolveScript
sys.path.append(r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules")
import DaVinciResolveScript as dvr

# Obtenir l'interface Resolve
resolve = dvr.scriptapp("Resolve")
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()

if not project:
    print("Aucun projet ouvert.")
    exit()

# Vérifier si un projet est ouvert et si une timeline existe
timelines_count = project.GetTimelineCount()
if timelines_count == 0:
    print("Aucune timeline dans ce projet.")
    exit()

print(f"Nombre de timelines dans le projet : {timelines_count}")

# Liste des timelines ajoutées à la queue pour la journalisation
added_timelines = []

# Parcourir les timelines
for i in range(1, timelines_count + 1):
    try:
        timeline = project.GetTimelineByIndex(i)
        timeline_name = timeline.GetName()

        # Exclure les timelines dont le nom contient "edit"
        if "edit" in timeline_name.lower():  # Utiliser lower() pour ne pas tenir compte de la casse
            print(f"Timeline ignorée (nom contient 'edit') : {timeline_name}")
            continue

        # Inclure seulement les timelines dont le nom contient "CAPS0"
        if "CAPS0" not in timeline_name:
            print(f"Timeline ignorée (nom ne contient pas 'CAPS0') : {timeline_name}")
            continue

        print(f"Traitement de la timeline : {timeline_name}")

        # Vérification des paramètres de la timeline
        timeline_width = timeline.GetSetting("timelineOutputResolutionWidth")
        timeline_height = timeline.GetSetting("timelineOutputResolutionHeight")
        timeline_fps = timeline.GetSetting("timelineFrameRate")

        # Journaliser la résolution et la fréquence d'images
        print(f"Résolution d'output : {timeline_width}x{timeline_height}")
        print(f"Fréquence d'images de la timeline : {timeline_fps}")

        if not timeline_width or not timeline_height or not timeline_fps:
            print(f"Paramètres de la timeline non valides pour {timeline_name}.")
            continue

        resolution = f"{timeline_width}x{timeline_height}"
        print(f"Résolution d'output détectée : {resolution}")

        # Paramètres d'export
        render_settings = {
            "Codec": "H264",  # Codec H264
            "Format": "mp4",  # Format MP4
            "Resolution": resolution,  # Résolution dynamique basée sur l'output de la timeline
            "Quality": "Automatic",  # "Automatic" ajuste le bitrate de manière optimale
            "Encoder": "NVIDIA",  # Utilisation du moteur d'encodage NVIDIA
            "Frame rate": "25",  # Fréquence d'images de 25 fps
            "Encoding Profile": "Auto",  # Profil d'encodage automatique
            "Key Frames": "Automatic",  # Frames clés automatiques
            "Frame reordering": True,  # Réordonnancement des frames
        }

        # Activer la timeline et ajouter un job à la Render Queue
        project.SetCurrentTimeline(timeline)

        # Debug - Afficher les paramètres de rendu avant l'ajout
        print(f"Paramètres de rendu pour {timeline_name}: {render_settings}")

        # Ajouter la timeline à la Render Queue en utilisant AddRenderJob
        success = project.AddRenderJob()

        if success:
            added_timelines.append(timeline_name)
            print(f"Timeline {timeline_name} ajoutée avec succès à la Render Queue.")
        else:
            print(f"Erreur lors de l'ajout de la timeline {timeline_name} à la Render Queue.")

        # Pause de 1 seconde entre les jobs pour éviter les erreurs de synchronisation
        time.sleep(1)

    except Exception as e:
        print(f"Erreur lors du traitement de la timeline {timeline_name}: {e}")

# Afficher les timelines ajoutées
print(f"Timelines ajoutées à la queue : {', '.join(added_timelines)}")
print("Script terminé.")
