# OTIO Review Tool — Guide de maintenance

## Lancement

```
launch.bat
```
Crée/réutilise le venv dans `C:\ProgramData\otio_review_tool\venv`, installe les dépendances, patche OpenRV, lance `app.py`.

---

## Demonstration

![](./demo/otiodemo_v0001.mp4)

## Structure des fichiers

### `app.py`
Point d'entrée. Crée la `QApplication`, applique la dark palette, instancie `MainWindow`.

### `config.py`
**Toutes les constantes** sont ici — chemins Prism, extensions media, FPS par défaut, chemins executables.

Points d'attention :
- `opentimelineio==0.16.0` est **figé** — ne pas mettre à jour sans tester avec OpenRV (le patch dans `launch.bat` est lié à cette version)
- `_find_latest_hiero()` détecte automatiquement la version Nuke installée sous `C:\Program Files\`. Le filtre `major < 17` exclut Nuke 17 (installation défectueuse sur la machine). À ajuster si une nouvelle version est installée.
- `HIERO_EXECUTABLE` : fallback sur Nuke 15.1v5 si aucune version < 17 n'est détectée

### `core/project.py`
Lit `pipeline.json` et `Prism.json` pour construire un objet `PrismProject` (FPS, départements, shot ranges).
- Si le projet n'a pas de `pipeline.json`, certains champs seront absents — le code tolère ça

### `core/scanner.py`
Parcourt `03_Production/Shots` et retourne des `ShotEntry[]`.
- `scan_versions()` cherche les dossiers de version (`v001`, `v002`...) dans l'ordre `RENDER_ROOTS` de `config.py`
- Le fallback de tâche suit `_FALLBACK_ORDER` dans ce fichier si la tâche demandée est absente d'un shot

### `core/media.py`
Détecte les séquences images et vidéos dans un dossier de version.
- Durée vidéo : parsing natif MP4/MOV (`mvhd`), puis `ffprobe`, puis fallback sur le shot range Prism
- Les séquences images utilisent le pattern `fichier.1001.exr` (point-séparateur Prism)

### `core/builder.py`
Construit le fichier `.otio`. **Un track par task**, tous dans un seul fichier.
- `build(shot_media_list)` groupe par task automatiquement
- `use_file_uri=True` pour Hiero (chemins `file:///`), `False` pour RV (chemins bruts)
- Les shots sans media reçoivent un `Gap` pour préserver la synchronisation temporelle

### `core/exceptions.py`
Hiérarchie d'exceptions custom. Rien de complexe.

---

## UI

### `ui/main_window.py`
Orchestrateur principal. Contient :
- `ScanWorker` (QThread) — le scan tourne hors thread principal
- `_export_timeline()` — construit et exporte le `.otio`
- `_launch_hiero()` — déploie le script startup Hiero puis lance l'exe
- `_launch_rv()` — lance OpenRV avec le fichier `.otio`

**Script startup Hiero** (`_HIERO_STARTUP_SCRIPT`) : déployé automatiquement dans `~/.nuke/Python/Startup/otio_review_autoload.py` à chaque lancement Hiero depuis le tool. Lit la variable d'env `OTIO_REVIEW_AUTOLOAD` et importe le `.otio` via `hiero.core.events.kStartup`. Si Hiero est lancé normalement (sans le tool), la variable est absente et le script ne fait rien.

### `ui/project_panel.py`
Combo des projets récents (lu depuis `Prism.json`) + bouton Browse.

### `ui/shot_panel.py`
Liste des shots avec inclusion/exclusion et filtre regex.

### `ui/step_panel.py`
Checkboxes des départements/tâches disponibles dans le projet.

### `ui/version_panel.py`
Choix de version : "Latest" automatique ou override manuel par shot.

### `ui/output_panel.py`
Nom de timeline, FPS, chemin output. L'output par défaut est auto-généré dans `%TEMP%`.

### `ui/log_panel.py`
Log coloré en temps réel (info / warning / error / success).

---

## Points critiques pour la maintenance

| Sujet | Détail |
|-------|--------|
| **opentimelineio** | Bloqué à `0.16.0`. `launch.bat` patche `otio_reader.py` d'OpenRV (`clip_if()` → `find_clips()`). Ne pas upgrader sans tester. |
| **Hiero < 17** | Le filtre `major < 17` dans `config._find_latest_hiero()` est intentionnel — Nuke 17 installé sur la machine est défectueux. Adapter si besoin. |
| **Startup script Hiero** | Écrasé à chaque lancement Hiero depuis le tool. Toute modification manuelle de `~/.nuke/Python/Startup/otio_review_autoload.py` sera perdue. Modifier `_HIERO_STARTUP_SCRIPT` dans `main_window.py`. |
| **Thread scan** | `ScanWorker` émet des signaux Qt — ne jamais appeler directement des méthodes UI depuis `core/`. |
| **ImageSequenceReference** | Utilisé à la place d'`ExternalReference` pour les séquences (compatibilité RV 2.0 + Hiero). |
| **Crash log** | `%TEMP%\otio_review_error.log` — consulter en premier en cas de crash silencieux. |

---

## Dépendances externes

- **Python 3.11/3.12**
- **PySide6 >= 6.4**
- **opentimelineio == 0.16.0** (figé)
- **OpenRV** : `C:\ILLOGIC_APP\OpenRV\bin\rv.exe`
- **Hiero/Nuke** : détecté automatiquement sous `C:\Program Files\Nuke*\`, version < 17
- **ffprobe** (optionnel) : utilisé pour la durée des vidéos si le parsing natif échoue
