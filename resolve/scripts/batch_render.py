import DaVinciResolveScript as dvr

# Obtenir l'interface Resolve
resolve = dvr.scriptapp("Resolve")
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()

if not project:
    print("Aucun projet ouvert.")
    exit()

# Obtenir toutes les timelines
timelines = project.GetTimelineCount()
if timelines == 0:
    print("Aucune timeline dans ce projet.")
    exit()

print(f"Nombre de timelines : {timelines}")

# Parcourir les timelines
for i in range(1, timelines + 1):
    timeline = project.GetTimelineByIndex(i)
    timeline_name = timeline.GetName()
    print(f"Ajout de la timeline : {timeline_name}")

    # Définir les paramètres de rendu
    render_settings = {
        "Codec": "H264",  # Changez à "H265" si nécessaire
        "Format": "mp4",  # Ou "mov" si QuickTime est nécessaire
        "Resolution": timeline.GetSetting("timelineResolutionWidth") + "x" + timeline.GetSetting("timelineResolutionHeight"),
        "Quality": "Automatic",  # Ou "Best" pour une qualité maximale
        "Bitrate": "10000",  # Ajustez selon vos besoins
        "UseMaxBitRate": True,
    }

    # Activer la timeline et ajouter un job à la Render Queue
    project.SetCurrentTimeline(timeline)
    if not project.AddRenderJob():
        print(f"Erreur lors de l'ajout de la timeline {timeline_name} à la Render Queue.")
    else:
        print(f"Timeline {timeline_name} ajoutée avec succès.")
