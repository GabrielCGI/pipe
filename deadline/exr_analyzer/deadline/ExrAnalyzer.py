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

_dialog = None


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

    # Confirmation
    PAD = "=" * 72
    lines = [PAD, f"  EXR Analyzer  —  {len(outputs)} job(s) selectionne(s)", PAD, ""]
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
            badge   = f"  ⚠  Deja analyse {count}x  —  derniere : {last_dt}"
        else:
            badge   = "  ✓  Pas encore analyse"

        lines.append(f"  {o['job_name']}")
        lines.append(f"  {ctx}")
        lines.append(badge)
        lines.append("")
    lines += [
        PAD,
        f"  Rapports : {REPORTS_DIR}",
        "",
        "  'Analyser'        ->  analyse  +  notification",
        "  'Analyser + HTML' ->  analyse  +  notification  +  librairie",
        PAD,
    ]

    confirm = _dialog.ShowMessageBox(
        "\n".join(lines),
        "EXR Analyzer",
        ["Analyser", "Analyser + HTML", "Annuler"]
    )

    if confirm == "Annuler":
        return

    open_html = (confirm == "Analyser + HTML")

    # Lancer les analyses
    launched = []
    errors   = []

    for o in outputs:
        try:
            _launch_analysis(o["path"], o["job_name"], open_html=open_html)
            launched.append(o["job_name"])
            ClientUtils.LogText(f"EXR Analyzer : analyse lancée pour {o['job_name']} ({o['path']})")
        except Exception as e:
            errors.append(f"{o['job_name']} : {e}")
            ClientUtils.LogText(f"EXR Analyzer : erreur sur {o['job_name']} — {e}")


    # Message final
    msg_lines = []
    if launched:
        msg_lines.append(f"{len(launched)} analyse(s) lancée(s) en arrière-plan.")
        msg_lines.append(f"Le dossier reports vient de s'ouvrir.")
        if open_html:
            msg_lines.append(f"Le rapport HTML s'ouvrira automatiquement une fois l'analyse terminée.")
    if errors:
        msg_lines.append("")
        msg_lines.append(f"{len(errors)} erreur(s) :")
        for e in errors:
            msg_lines.append(f"  • {e}")

    _dialog.ShowMessageBox("\n".join(msg_lines), "EXR Analyzer")


def _launch_analysis(output_dir, job_name, open_html=False):
    """Lance analyze_exr.py en arrière-plan via le Python studio."""
    import datetime

    analyze_script = os.path.join(TOOL_ROOT, "analyze_exr.py")

    # Créer le dossier logs et ouvrir le fichier immédiatement
    os.makedirs(LOGS_DIR, exist_ok=True)
    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(LOGS_DIR, f"deadline_{ts}.log")
    log_fh   = open(log_path, "w", encoding="utf-8", buffering=1)
    machine  = os.environ.get("COMPUTERNAME", "unknown")
    user     = os.environ.get("USERNAME",     "unknown")
    log_fh.write(f"[{ts}] EXR Analyzer lancé\n")
    log_fh.write(f"  machine    : {machine}\n")
    log_fh.write(f"  user       : {user}\n")
    log_fh.write(f"  job_name   : {job_name}\n")
    log_fh.write(f"  output_dir : {output_dir}\n")
    log_fh.write(f"  python     : {PYTHON_EXE}\n")
    log_fh.write(f"  script     : {analyze_script}\n\n")
    log_fh.flush()

    # Appendre SITE_PKG sans écraser le PYTHONPATH existant
    env = dict(os.environ)
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = SITE_PKG + os.pathsep + existing_pp if existing_pp else SITE_PKG

    cmd = [
        PYTHON_EXE,
        analyze_script,
        output_dir,
        "--reports-dir", REPORTS_DIR,
        "--log-dir",     LOGS_DIR,
        "--job-name",    job_name,
    ]
    if open_html:
        cmd.append("--open-html")

    subprocess.Popen(
        cmd,
        env=env,
        stdout=log_fh,
        stderr=log_fh,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
