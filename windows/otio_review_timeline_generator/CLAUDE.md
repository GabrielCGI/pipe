# OTIO Review Timeline Generator

## Vue d'ensemble

Application desktop PySide6 (Qt6) pour générer des timelines OpenTimelineIO (OTIO) à partir de projets Prism. Scanne la structure Prism, découvre les médias rendus, exporte des fichiers `.otio` par tâche ouvrable dans OpenRV.

**Stack** : Python 3.11/3.12 · PySide6 · opentimelineio==0.16.0 (fixé pour compatibilité OpenRV)

**Lancement** : `launch.bat` (gère le venv dans `C:\ProgramData\otio_review_tool\venv`)

---

## Structure du projet

```
app.py              # Point d'entrée, QApplication, dark palette
config.py           # Toutes les constantes (chemins Prism, extensions, RV path)
launch.bat          # Launcher Windows : venv + deps + patch OpenRV
requirements.txt    # opentimelineio==0.16.0, PySide6>=6.4
core/
  project.py        # PrismProject, ProjectLoader — lit pipeline.json / Prism.json
  scanner.py        # ProjectScanner — parcourt 03_Production/Shots
  media.py          # MediaDiscovery — détecte séquences images et vidéos
  version_cache.py  # VersionCache — cache JSON de complétude des versions rendues
  builder.py        # TimelineBuilder — construit et exporte l'otio.Timeline
  exceptions.py     # Hiérarchie d'exceptions custom
ui/
  main_window.py    # MainWindow + ScanWorker (QThread)
  project_panel.py  # Sélection projet (combo récents + browse)
  shot_panel.py     # Liste shots avec include/exclude + filtre regex
  step_panel.py     # Checkboxes départements/tâches
  version_panel.py  # Latest auto ou override manuel par shot
  output_panel.py   # Nom timeline, FPS, chemin output
  log_panel.py      # Log coloré en temps réel
```

---

## Config clé (config.py)

| Constante | Valeur |
|-----------|--------|
| Shots root | `03_Production/Shots` |
| Pipeline config | `00_Pipeline/pipeline.json` |
| Shot ranges | `00_Pipeline/Shotinfo/shotInfo.json` |
| Version cache | `04_Resources/otio/version_cache.json` |
| Render roots (priorité) | `Renders/2dRender` → `Renders/3dRender` → `Playblasts` |
| Image ext | `.exr .dpx .tiff .tif .png .jpg .jpeg` |
| Video ext | `.mp4 .mov .mxf .avi` |
| Frame pattern | `file.1001.exr` (Prism dot-separated) |
| FPS défaut | 25.0 |
| OpenRV | `C:\ILLOGIC_APP\OpenRV\bin\rv.exe` |
| Prism config | `~/Documents/Prism2/Prism.json` (Windows) |

---

## Flux de données

```
ProjectLoader.from_path()
  → PrismProject (fps, departments, shot_ranges)
    → ProjectScanner.scan_shots()
      → ShotEntry[] (sequence/shot/frames/has_shot_range)
        → ProjectScanner.scan_versions()
          → VersionCache.load()
            → ProjectScanner.find_complete_media()
              → MediaDiscovery.find_in_version_folder()
                → MediaItem (path, type, frame_start/end, abstract_path, is_complete)
                  → TimelineBuilder.build()
                    → otio.Timeline (1 Track par tâche)
                      → .otio file(s)
            → VersionCache.flush()
```

---

## Points importants

- **opentimelineio==0.16.0** est fixé — ne pas mettre à jour sans tester avec OpenRV. `launch.bat` patche `otio_reader.py` d'OpenRV (`clip_if()` → `find_clips()`).
- **ImageSequenceReference** utilisé pour les séquences (compatibilité RV 2.0), pas ExternalReference.
- **ScanWorker** (QThread) — le scan tourne hors thread principal. Les signaux `shot_scanned` / `scan_complete` / `scan_error` pilotent l'UI.
- **Fallback tâche** : si la tâche demandée est absente sur un shot, `ScanWorker` suit l'ordre `_FALLBACK_ORDER` (Compo → MattePaint → FX → ...).
- **Durée vidéo** : parsing natif des boîtes MP4/MOV (mvhd), puis ffprobe si dispo, sinon frame range Prism ou 100 frames.
- **Métadonnées OTIO** : chaque clip embarque un dict `prism` (sequence, shot, task, version, frame range, media type) pour round-tripping.
- **Output auto** : `%TEMP%/{date}_{project}_{tasks}_timeline_v{n}.otio`
- **Crash log** : `%TEMP%\otio_review_error.log`
- **Détection de versions incomplètes** : `find_complete_media()` remonte les versions de la plus récente à la plus ancienne et retourne la première complète. Deux stratégies selon `ShotEntry.has_shot_range` :
  - `has_shot_range=True` (shotInfo.json présent) : compare `frame_count` réel vs `frame_count` attendu.
  - `has_shot_range=False` (ex. projet Kitsu sans shotInfo.json) : compare `frame_count` de vN vs v(N-1). Si vN a moins de frames que sa version précédente, elle est considérée incomplète.
- **VersionCache** : cache JSON dans `04_Resources/otio/version_cache.json`. Les entrées `complete=True` évitent le re-scan disque (projets avec shotInfo.json uniquement — en mode fallback, le disque est toujours relu). Les entrées `complete=False` sont ignorées comme cache positif.
