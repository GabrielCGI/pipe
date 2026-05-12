"""
ExrAnalyzer.py  —  Script Deadline Monitor
Clic droit sur un job > Scripts > EXR Analyzer

Installation :
    Copier ce fichier dans <DeadlineRepository>/custom/scripts/Jobs/
"""

from __future__ import absolute_import

import os
import re
import json
import subprocess

from System.IO import Path

from Deadline.Scripting import ClientUtils, FrameUtils, MonitorUtils, PathUtils, RepositoryUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

# ── Chemins studio ────────────────────────────────────────────────────────────
TOOL_ROOT   = r"R:\pipeline\pipe\deadline\exr_analyzer"
PYTHON_EXE  = r"C:\Program Files\Thinkbox\Deadline10\bin\python3\python.exe"
SITE_PKG    = r"R:\pipeline\networkInstall\python_shares\python310_deadline_discord_pkgs\Lib\site-packages"
REPORTS_DIR = r"R:\pipeline\pipe\deadline\exr_analyzer\reports"
LOGS_DIR    = r"R:\devToto\Claude\exr-analyzer\logs-deadline"
# ─────────────────────────────────────────────────────────────────────────────

_dialog       = None
_confirm_dlg  = None
_dialog_ok    = False


def _parse_path_key(output_dir):
    """
    Extrait (prod, seq, shot, layer) depuis le chemin output.
    Ancré sur 03_Production, même logique que analyze_exr.py.
    Retourne None si non reconnu.
    """
    parts       = re.split(r'[\\/]', output_dir.replace('\\', '/'))
    parts_lower = [p.lower() for p in parts]

    try:
        prod_idx = next(i for i, p in enumerate(parts_lower) if p == "03_production")
    except StopIteration:
        return None

    prod      = parts[prod_idx - 1] if prod_idx > 0 else "unknown"
    type_part = parts_lower[prod_idx + 1] if prod_idx + 1 < len(parts_lower) else ""

    # Layer = premier élément après 3drender qui n'est pas une version
    layer = "UNKNOWN"
    for i, p in enumerate(parts_lower):
        if p == "3drender" and i + 1 < len(parts):
            candidate = parts[i + 1]
            if not re.match(r'^v\d+', candidate, re.IGNORECASE):
                layer = candidate
                break

    if type_part == "shots":
        seq  = parts[prod_idx + 2] if prod_idx + 2 < len(parts) else "UNKNOWN"
        shot = parts[prod_idx + 3] if prod_idx + 3 < len(parts) else "UNKNOWN"
        return {"prod": prod, "seq": seq, "shot": shot, "layer": layer}

    elif type_part == "assets":
        category = parts[prod_idx + 2] if prod_idx + 2 < len(parts) else "UNKNOWN"
        name     = parts[prod_idx + 3] if prod_idx + 3 < len(parts) else "UNKNOWN"
        return {"prod": prod, "seq": category, "shot": name, "layer": layer}

    return None


def _find_existing_analyses(output_dir):
    """
    Cherche dans reports/jobs/ les manifests JSON correspondant à ce chemin.
    Retourne une liste de dicts {ts, html} triée du plus récent au plus ancien.
    """
    jobs_dir = os.path.join(REPORTS_DIR, "jobs")
    if not os.path.isdir(jobs_dir):
        return []

    key = _parse_path_key(output_dir)
    if key is None:
        return []

    matches = []
    for fname in os.listdir(jobs_dir):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(jobs_dir, fname)
        try:
            with open(fpath, encoding="utf-8") as f:
                m = json.load(f)
            if (m.get("prod")  == key["prod"]  and
                m.get("seq")   == key["seq"]   and
                m.get("shot")  == key["shot"]  and
                m.get("layer") == key["layer"]):
                matches.append({"ts": m.get("ts", ""), "html": m.get("html", fname)})
        except Exception:
            continue

    matches.sort(key=lambda x: x["ts"], reverse=True)
    return matches


def _on_analyser_clicked():
    global _dialog_ok
    _dialog_ok = True
    if _confirm_dlg is not None:
        _confirm_dlg.CloseDialog()


def _on_cancel_clicked():
    global _dialog_ok
    _dialog_ok = False
    if _confirm_dlg is not None:
        _confirm_dlg.CloseDialog()


def __main__():
    global _dialog
    _dialog = DeadlineScriptDialog()

    selected_jobs = MonitorUtils.GetSelectedJobs()

    if len(selected_jobs) == 0:
        _dialog.ShowMessageBox("Aucun job sélectionné.", "EXR Analyzer")
        return

    # Construire la liste des outputs à analyser
    outputs = []
    for job in selected_jobs:
        if len(job.JobOutputDirectories) == 0:
            ClientUtils.LogText(f"EXR Analyzer : job {job.JobId} sans output directory, ignoré.")
            continue

        output_dir = job.JobOutputDirectories[0]
        output_dir = RepositoryUtils.CheckPathMapping(output_dir, False)
        output_dir = PathUtils.ToPlatformIndependentPath(output_dir)

        existing = _find_existing_analyses(output_dir)
        outputs.append({
            "job_id":   job.JobId,
            "job_name": job.JobName,
            "path":     output_dir,
            "existing": existing,
        })

    if len(outputs) == 0:
        _dialog.ShowMessageBox(
            "Aucun job sélectionné ne contient de output directory.",
            "EXR Analyzer"
        )
        return

    # ── Dialog de confirmation ────────────────────────────────────────────
    global _confirm_dlg, _dialog_ok
    _dialog_ok   = False
    _confirm_dlg = DeadlineScriptDialog()
    _confirm_dlg.SetTitle("EXR Analyzer")

    # Infos jobs
    info_lines = [f"EXR Analyzer  —  {len(outputs)} job(s) selectionne(s)", ""]
    for o in outputs:
        existing = o.get("existing", [])
        key      = _parse_path_key(o["path"]) or {}
        prod     = key.get("prod",  "?")
        seq      = key.get("seq",   "?")
        shot     = key.get("shot",  "?")
        layer    = key.get("layer", "?")
        ctx      = f"{prod}  >  {seq}  >  {shot}  >  {layer}"

        if existing:
            last_ts = existing[0]["ts"]
            last_dt = last_ts[:4]+"-"+last_ts[4:6]+"-"+last_ts[6:8]+" "+last_ts[9:11]+":"+last_ts[11:13]
            count   = len(existing)
            badge   = f"Deja analyse {count}x  —  derniere : {last_dt}"
        else:
            badge   = "Pas encore analyse"

        info_lines.append(o["job_name"])
        info_lines.append(ctx)
        info_lines.append(badge)
        info_lines.append("")

    # Section info
    _confirm_dlg.AddGrid()
    _confirm_dlg.AddControlToGrid(
        "InfoLabel", "LabelControl", "\n".join(info_lines), 0, 0, colSpan=2
    )
    _confirm_dlg.EndGrid()

    # Section options (checkboxes avec label intégré)
    _confirm_dlg.AddGrid()
    _confirm_dlg.AddSelectionControlToGrid(
        "PixelCheck", "CheckBoxControl", False,
        "Analyse valeur de pixel (plus long)", 0, 0,
        "Si decoche, seules les metadonnees EXR sont lues (rapide).",
    )
    _confirm_dlg.AddSelectionControlToGrid(
        "HtmlCheck", "CheckBoxControl", False,
        "Ouvrir le rapport HTML une fois termine", 1, 0,
        "Ouvre la librairie HTML dans le navigateur a la fin de l'analyse.",
    )
    _confirm_dlg.AddSelectionControlToGrid(
        "DebugCheck", "CheckBoxControl", False,
        "Mode debug (afficher les logs dans une console)", 2, 0,
        "Ouvre une fenetre CMD pour voir l'avancement et les logs en direct (pas de fichier log).",
    )
    _confirm_dlg.EndGrid()

    # Boutons
    _confirm_dlg.AddGrid()
    _confirm_dlg.AddHorizontalSpacerToGrid("BtnSpacer", 0, 0)
    btn_ok = _confirm_dlg.AddControlToGrid("OkBtn", "ButtonControl", "Analyser", 0, 1, expand=False)
    btn_ok.ValueModified.connect(_on_analyser_clicked)
    btn_cancel = _confirm_dlg.AddControlToGrid("CancelBtn", "ButtonControl", "Annuler", 0, 2, expand=False)
    btn_cancel.ValueModified.connect(_on_cancel_clicked)
    _confirm_dlg.EndGrid()

    _confirm_dlg.ShowDialog(True)

    if not _dialog_ok:
        return

    pixel_analysis = _confirm_dlg.GetValue("PixelCheck")
    open_html      = _confirm_dlg.GetValue("HtmlCheck")
    debug_mode     = _confirm_dlg.GetValue("DebugCheck")
    metadata_only  = not pixel_analysis

    # Lancer les analyses (un seul subprocess superviseur, jobs en séquentiel)
    errors = []
    try:
        _launch_batch(outputs, open_html=open_html, metadata_only=metadata_only, debug=debug_mode)
        for o in outputs:
            ClientUtils.LogText(f"EXR Analyzer : queue {o['job_name']} ({o['path']})")
    except Exception as e:
        errors.append(str(e))
        ClientUtils.LogText(f"EXR Analyzer : erreur — {e}")

    # Message final
    mode = "metadata uniquement" if metadata_only else "pixels + metadata"
    msg_lines = []
    if not errors:
        where = "dans une console CMD" if debug_mode else "en arriere-plan"
        msg_lines.append(f"{len(outputs)} job(s) en file {where} (sequentiel)  [{mode}].")
        if open_html:
            msg_lines.append("Le rapport HTML s'ouvrira automatiquement a la fin.")
    if errors:
        msg_lines.append("")
        msg_lines.append("Erreur(s) :")
        for e in errors:
            msg_lines.append(f"  * {e}")

    _dialog.ShowMessageBox("\n".join(msg_lines), "EXR Analyzer")


def _build_analyze_cmd(output_dir, job_name, open_html, metadata_only, with_log_dir):
    """Construit la commande analyze_exr.py pour un job (renvoie liste args)."""
    cmd = [
        PYTHON_EXE,
        os.path.join(TOOL_ROOT, "analyze_exr.py"),
        output_dir,
        "--reports-dir", REPORTS_DIR,
        "--job-name",    job_name,
    ]
    if open_html:
        cmd.append("--open-html")
    if metadata_only:
        cmd.append("--metadata-only")
    if with_log_dir:
        cmd += ["--log-dir", LOGS_DIR]
    return cmd


def _launch_batch(outputs, open_html=False, metadata_only=True, debug=False):
    """Lance toutes les analyses dans UN SEUL subprocess, en séquentiel.

    Évite N process parallèles qui saturent réseau/RAM quand on sélectionne
    plusieurs jobs à la fois. Génère un .bat temporaire qui enchaîne les
    appels à analyze_exr.py.

    debug=True  : console CMD ouverte, reste ouverte après la fin
    debug=False : process caché, log fichier unique
    """
    import datetime
    import tempfile

    ts      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    machine = os.environ.get("COMPUTERNAME", "unknown")
    user    = os.environ.get("USERNAME",     "unknown")

    env = dict(os.environ)
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = SITE_PKG + os.pathsep + existing_pp if existing_pp else SITE_PKG

    # Construire le .bat
    bat_lines = [
        "@echo off",
        f"title EXR Analyzer - {len(outputs)} job(s)",
    ]
    for i, o in enumerate(outputs, 1):
        cmd = _build_analyze_cmd(
            o["path"], o["job_name"],
            open_html=open_html, metadata_only=metadata_only,
            with_log_dir=not debug,
        )
        bat_lines.append("")
        bat_lines.append(f'echo === [{i}/{len(outputs)}] {o["job_name"]} ===')
        bat_lines.append(subprocess.list2cmdline(cmd))
    bat_lines.append("")
    bat_lines.append(f'echo === [Termine - {len(outputs)} job(s) traite(s)] ===')

    bat_dir = LOGS_DIR if not debug else tempfile.gettempdir()
    os.makedirs(bat_dir, exist_ok=True)
    bat_path = os.path.join(bat_dir, f"exr_analyzer_batch_{ts}.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write("\r\n".join(bat_lines) + "\r\n")

    if debug:
        # /k garde la fenêtre ouverte après la fin du .bat
        subprocess.Popen(
            f'cmd /k call "{bat_path}"',
            env=env,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        return

    # Mode normal : log fichier superviseur
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_path = os.path.join(LOGS_DIR, f"deadline_batch_{ts}.log")
    log_fh   = open(log_path, "w", encoding="utf-8", buffering=1)
    log_fh.write(f"[{ts}] EXR Analyzer batch lance\n")
    log_fh.write(f"  machine : {machine}\n")
    log_fh.write(f"  user    : {user}\n")
    log_fh.write(f"  jobs    : {len(outputs)}\n")
    for i, o in enumerate(outputs, 1):
        log_fh.write(f"    [{i}] {o['job_name']}  ->  {o['path']}\n")
    log_fh.write(f"  bat     : {bat_path}\n\n")
    log_fh.flush()

    subprocess.Popen(
        [bat_path],
        env=env,
        stdout=log_fh,
        stderr=log_fh,
        creationflags=subprocess.CREATE_NO_WINDOW,
        shell=False,
    )
