import DaVinciResolveScript as dvr

# Obtenir l'interface Resolve
resolve = dvr.scriptapp("Resolve")
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()

if not project:
    print("Aucun projet ouvert.")
    exit()

# Obtenir toutes les timelines
timelines_count = project.GetTimelineCount()
if timelines_count == 0:
    print("Aucune timeline dans ce projet.")
    exit()

print(f"Nombre de timelines dans le projet : {timelines_count}")

# Parcourir les timelines
for i in range(1, timelines_count + 1):
    timeline = project.GetTimelineByIndex(i)
    timeline_name = timeline.GetName()

    # Filtrer par nom de timeline contenant "CAPS0"
    if "CAPS0" not in timeline_name:
        print(f"Timeline ignorée : {timeline_name}")
        continue

    print(f"Traitement de la timeline : {timeline_name}")

    # Définir les paramètres de rendu
    # Utiliser la résolution d'output de la timeline
    timeline_width = timeline.GetSetting("timelineOutputResolutionWidth")
    timeline_height = timeline.GetSetting("timelineOutputResolutionHeight")

    if not timeline_width or not timeline_height:
        print(f"Impossible de récupérer la résolution d'output pour la timeline {timeline_name}.")
        continue

    resolution = f"{timeline_width}x{timeline_height}"
    print(f"Résolution d'output détectée : {resolution}")

    render_settings = {
        "Codec": "H264",  # Changez à "H265" si nécessaire
        "Format": "mp4",  # Ou "mov" si QuickTime est nécessaire
        "Resolution": resolution,  # Résolution dynamique basée sur l'output de la timeline
        "Quality": "Automatic",  # Ou "Best" pour une qualité maximale
        "Bitrate": "10000",  # Ajustez selon vos besoins
        "UseMaxBitRate": True,
    }

    # Activer la timeline et ajouter un job à la Render Queue
    project.SetCurrentTimeline(timeline)
    success = project.AddRenderJob()
    
    if not success:
        print(f"Erreur lors de l'ajout de la timeline {timeline_name} à la Render Queue.")
    else:
        print(f"Timeline {timeline_name} ajoutée avec succès à la Render Queue.")

print("Script terminé.")
