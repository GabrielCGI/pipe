"""
analyze_exr.py  —  Wrapper de lancement pour exr_analyzer
- Détecte SQ/shot/layer depuis le chemin ou le nom de fichier
- Lance l'analyse et place le HTML dans <reports-dir>/jobs/
- Régénère <reports-dir>/index.html (librairie de tous les rapports)

Usage :
    python analyze_exr.py <chemin_fichier_ou_dossier>
                          [--reports-dir <dir>]
                          [--log-dir     <dir>]
                          [--job-name    <str>]
"""

import sys
import re
import subprocess
import datetime
import argparse
from pathlib import Path
from html import escape


# ──────────────────────────────────────────────
#  Parsing du chemin (shot ou asset)
# ──────────────────────────────────────────────

def _find_layer_after_3drender(parts: list) -> str:
    """Premier dossier après '3dRender' qui n'est pas une version (v###)."""
    for i, p in enumerate(parts):
        if p.lower() == "3drender" and i + 1 < len(parts):
            candidate = parts[i + 1]
            if not re.match(r'^v\d+', candidate, re.IGNORECASE):
                return candidate
    return "UNKNOWN"


def parse_path_info(input_path: Path) -> dict:
    """
    Parse le chemin en s'ancrant sur '03_Production' puis par position.

    Shot  : <prod>/03_Production/Shots/<SEQ>/<SHOT>/Renders/3dRender/<LAYER>/v###/pass
    Asset : <prod>/03_Production/Assets/<CAT>/<NAME>/Renders/3dRender/<LAYER>/v###/pass
    """
    parts       = list(input_path.parts)
    parts_lower = [p.lower() for p in parts]

    prod_idx = next((i for i, p in enumerate(parts_lower) if p == "03_production"), None)
    if prod_idx is None:
        return {"type": "unknown", "prod": "UNKNOWN", "prefix": "UNKNOWN",
                "group": "UNKNOWN", "sub": "UNKNOWN", "label": "UNKNOWN"}

    prod      = parts[prod_idx - 1] if prod_idx > 0 else "unknown"
    type_part = parts_lower[prod_idx + 1] if prod_idx + 1 < len(parts_lower) else ""
    layer     = _find_layer_after_3drender(parts)

    if type_part == "shots":
        seq  = parts[prod_idx + 2] if prod_idx + 2 < len(parts) else "UNKNOWN"
        shot = parts[prod_idx + 3] if prod_idx + 3 < len(parts) else "UNKNOWN"
        return {
            "type":   "shot",
            "prod":   prod,
            "seq":    seq,
            "shot":   shot,
            "layer":  layer,
            "prefix": f"{seq}_{shot}_{layer}",
            "group":  seq,
            "sub":    shot,
            "label":  layer,
        }

    elif type_part == "assets":
        category = parts[prod_idx + 2] if prod_idx + 2 < len(parts) else "UNKNOWN"
        name     = parts[prod_idx + 3] if prod_idx + 3 < len(parts) else "UNKNOWN"
        return {
            "type":     "asset",
            "prod":     prod,
            "category": category,
            "name":     name,
            "layer":    layer,
            "prefix":   f"ASSET_{category}_{name}_{layer}",
            "group":    category,
            "sub":      name,
            "label":    layer,
        }

    return {"type": "unknown", "prod": "UNKNOWN", "prefix": "UNKNOWN",
            "group": "UNKNOWN", "sub": "UNKNOWN", "label": "UNKNOWN"}


def build_glob(input_path: Path) -> str:
    if input_path.is_dir():
        return str(input_path)
    stem = input_path.stem
    base = re.sub(r'\.\d+$', '', stem)
    return str(input_path.parent / f"{base}.*.exr")


# ──────────────────────────────────────────────
#  Manifest & Librairie
# ──────────────────────────────────────────────

def write_manifest(html_path: Path, info: dict, ts: str, exr_path: str = ""):
    """Ecrit un .json de métadonnées à côté du HTML pour la librairie."""
    import json as _json
    manifest = {
        "prod":     info.get("prod",  "UNKNOWN"),
        "type":     info.get("type",  "unknown"),
        "seq":      info.get("seq",   info.get("group", "UNKNOWN")),
        "shot":     info.get("shot",  info.get("sub",   "UNKNOWN")),
        "layer":    info.get("layer", info.get("label", "UNKNOWN")),
        "is_asset": info.get("type") == "asset",
        "ts":       ts,
        "html":     html_path.name,
        "exr_path": exr_path,
    }
    html_path.with_suffix(".json").write_text(
        _json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def send_notification(title: str, line1: str, line2: str = ""):
    """
    Envoie une toast notification Windows via PowerShell (sans dépendance externe).
    Non-bloquant — le process PowerShell se termine seul.
    """
    xml = (
        "<toast>"
        "<visual><binding template='ToastGeneric'>"
        f"<text>{escape(title)}</text>"
        f"<text>{escape(line1)}</text>"
        + (f"<text>{escape(line2)}</text>" if line2 else "") +
        "</binding></visual>"
        "</toast>"
    )
    ps = (
        "Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null;"
        "[void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI, ContentType=WindowsRuntime];"
        "[void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType=WindowsRuntime];"
        f"$xml = '{xml.replace(chr(39), chr(34))}';"
        "$doc = [Windows.Data.Xml.Dom.XmlDocument]::new();"
        "$doc.LoadXml($xml);"
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($doc);"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
        "'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe'"
        ").Show($toast)"
    )
    try:
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-NonInteractive", "-Command", ps],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception as e:
        print(f"  [notif] Impossible d'envoyer la notification Windows : {e}")


def _parse_report_fallback(filename: str):
    """Fallback pour anciens rapports sans .json."""
    m = re.match(r'^(.+?)_(\d{8})_(\d{6})\.html$', filename)
    if not m:
        return None
    try:
        dt = datetime.datetime.strptime(m.group(2) + m.group(3), "%Y%m%d%H%M%S")
    except ValueError:
        return None
    prefix = m.group(1)
    ms = re.match(r'^([A-Z0-9_]+)_(SH\d+)_([A-Za-z]+)$', prefix)
    if ms:
        return {"prod": "UNKNOWN", "type": "shot", "seq": ms.group(1),
                "shot": ms.group(2), "layer": ms.group(3), "is_asset": False,
                "ts": dt.strftime("%Y%m%d_%H%M%S"), "html": filename}, dt
    ma = re.match(r'^ASSET_(\w+)_(\w+)_(\w+)$', prefix)
    if ma:
        return {"prod": "UNKNOWN", "type": "asset", "seq": ma.group(1),
                "shot": ma.group(2), "layer": ma.group(3), "is_asset": True,
                "ts": dt.strftime("%Y%m%d_%H%M%S"), "html": filename}, dt
    return None


def _sid(s: str) -> str:
    """Sanitize string for use as HTML id."""
    return re.sub(r'[^A-Za-z0-9]', '_', s)


def parse_report_name(filename: str):
    """
    Extrait (info_dict, datetime) depuis un nom de rapport.
    Formats supportés :
      SQ050_SH0140_CHARS_20260319_133349.html           → shot
      ASSET_Characters_bucky_turnTable_20260319_...html  → asset
    Retourne None si le nom ne correspond pas.
    """
    m = re.match(r'^(.+?)_(\d{8})_(\d{6})\.html$', filename)
    if not m:
        return None
    prefix = m.group(1)
    try:
        dt = datetime.datetime.strptime(m.group(2) + m.group(3), "%Y%m%d%H%M%S")
    except ValueError:
        return None

    # Shot : SQ050_SH0140_CHARS
    ms = re.match(r'^(SQ\d+)_(SH\d+)_([A-Za-z]+)$', prefix)
    if ms:
        return {
            "type":   "shot",
            "prefix": prefix,
            "group":  ms.group(1),
            "sub":    ms.group(2),
            "label":  ms.group(3),
        }, dt

    # Asset : ASSET_<Category>_<name>_<layer>
    ma = re.match(r'^ASSET_(\w+)_(\w+)_(\w+)$', prefix)
    if ma:
        return {
            "type":   "asset",
            "prefix": prefix,
            "group":  f"ASSET_{ma.group(1)}",
            "sub":    ma.group(2),
            "label":  ma.group(3),
        }, dt

    return None


def generate_library(reports_dir: Path):
    """Scanne reports/jobs/ et régénère reports/index.html."""
    import json as _json

    jobs_dir = reports_dir / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)

    reports = []
    for html_file in sorted(jobs_dir.glob("*.html")):
        json_file = html_file.with_suffix(".json")
        if json_file.exists():
            try:
                manifest = _json.loads(json_file.read_text(encoding="utf-8"))
                dt = datetime.datetime.strptime(manifest["ts"], "%Y%m%d_%H%M%S")
                reports.append({**manifest, "dt": dt, "file": f"jobs/{html_file.name}"})
                continue
            except Exception:
                pass
        parsed = _parse_report_fallback(html_file.name)
        if parsed:
            meta, dt = parsed
            reports.append({**meta, "dt": dt, "file": f"jobs/{html_file.name}"})

    reports.sort(key=lambda r: r["dt"], reverse=True)

    # ── Arbre 4 niveaux : prod > seq > shot > layer ───────────────────
    tree = {}
    for r in reports:
        (tree
         .setdefault(r.get("prod", "UNKNOWN"), {})
         .setdefault(r.get("seq",  "UNKNOWN"), {})
         .setdefault(r.get("shot", "UNKNOWN"), {})
         .setdefault(r.get("layer","UNKNOWN"), [])
         .append(r))

    default_src = reports[0]["file"] if reports else ""

    # ── Sidebar HTML ──────────────────────────────────────────────────
    sidebar_items = []
    for prod in sorted(tree):
        pid          = _sid(prod)
        prod_display = prod.replace("_", " ").title()
        sidebar_items += [
            f'<div class="prod-group">',
            f'  <div class="prod-label" onclick="toggleSection(\'p-{pid}\')">',
            f'    <span class="arrow" id="arr-p-{pid}">▶</span>',
            f'    {escape(prod_display)}',
            f'  </div>',
            f'  <div class="prod-children" id="p-{pid}" style="display:none">',
        ]
        for seq in sorted(tree[prod]):
            sid = _sid(f"{prod}_{seq}")
            has_asset = any(
                r.get("is_asset", False)
                for sh in tree[prod][seq].values()
                for runs in sh.values() for r in runs
            )
            badge = '<span class="tag-asset">ASSET</span> ' if has_asset else ''
            sidebar_items += [
                f'    <div class="seq-group">',
                f'      <div class="seq-label" onclick="toggleSection(\'s-{sid}\')">',
                f'        <span class="arrow" id="arr-s-{sid}">▶</span>',
                f'        {badge}{escape(seq)}',
                f'      </div>',
                f'      <div class="seq-children" id="s-{sid}" style="display:none">',
            ]
            for shot in sorted(tree[prod][seq]):
                shid = _sid(f"{prod}_{seq}_{shot}")
                sidebar_items += [
                    f'        <div class="shot-group">',
                    f'          <div class="shot-label" onclick="toggleSection(\'sh-{shid}\')">',
                    f'            <span class="arrow" id="arr-sh-{shid}">▶</span>',
                    f'            <span class="lbl-shot">{escape(shot)}</span>',
                    f'          </div>',
                    f'          <div class="shot-children" id="sh-{shid}" style="display:none">',
                ]
                for layer in sorted(tree[prod][seq][shot]):
                    runs   = tree[prod][seq][shot][layer]
                    run_id = _sid(f"{prod}_{seq}_{shot}_{layer}")
                    sidebar_items += [
                        f'            <div class="layer-group" id="lg-{run_id}">',
                        f'              <div class="layer-label" onclick="toggleLayer(\'{run_id}\')">',
                        f'                <span class="arrow" id="arr-{run_id}">▶</span>',
                        f'                <span class="lbl-layer">{escape(layer)}</span>',
                        f'                <span class="run-count">{len(runs)}</span>',
                        f'              </div>',
                        f'              <div class="run-list" id="rl-{run_id}" style="display:none">',
                    ]
                    for i, run in enumerate(runs):
                        cls = "run-item latest" if i == 0 else "run-item"
                        tag = "<span class='tag-latest'>latest</span>" if i == 0 else ""
                        dt_display = run["dt"].strftime("%Y-%m-%d  %H:%M")
                        exr_raw = run.get("exr_path", "")
                        sidebar_items.append(
                            f'                <div class="{cls}" onclick="loadReport(\'{run["file"]}\', this)"'
                            f' data-file="{run["file"]}"'
                            f' data-exr="{escape(exr_raw)}">'
                            f'                  {escape(dt_display)} {tag}'
                            f'                </div>'
                        )
                    sidebar_items += [
                        f'              </div>',  # run-list
                        f'            </div>',    # layer-group
                    ]
                sidebar_items += [
                    f'          </div>',  # shot-children
                    f'        </div>',    # shot-group
                ]
            sidebar_items += [
                f'      </div>',  # seq-children
                f'    </div>',    # seq-group
            ]
        sidebar_items += [
            f'  </div>',  # prod-children
            f'</div>',    # prod-group
        ]

    sidebar_html = "\n".join(sidebar_items)

    total       = len(reports)
    shots_count = sum(len(v) for v in tree.values())
    now         = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>EXR Analyzer — Library</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ display: flex; height: 100vh; font-family: 'Segoe UI', sans-serif;
          background: #1a1a1a; color: #ccc; overflow: hidden; }}

  #sidebar {{
    width: 300px; min-width: 200px; max-width: 480px;
    background: #111; border-right: 1px solid #2a2a2a;
    display: flex; flex-direction: column; overflow: hidden;
    resize: horizontal;
  }}
  #sidebar-header {{
    padding: 14px 16px 10px; background: #0d0d0d;
    border-bottom: 1px solid #222;
  }}
  #sidebar-header h1 {{ font-size: 13px; font-weight: 600; color: #e0e0e0; letter-spacing:.5px; }}
  #sidebar-header .meta {{ font-size: 10px; color: #555; margin-top: 4px; }}
  #sidebar-search {{
    padding: 8px 10px; background: #0d0d0d; border-bottom: 1px solid #1e1e1e;
  }}
  #sidebar-search input {{
    width: 100%; background: #1e1e1e; border: 1px solid #333;
    color: #ccc; padding: 5px 8px; border-radius: 4px; font-size: 12px; outline: none;
  }}
  #sidebar-search input:focus {{ border-color: #555; }}
  #sidebar-scroll {{ flex: 1; overflow-y: auto; padding: 6px 0; }}
  #sidebar-scroll::-webkit-scrollbar {{ width: 4px; }}
  #sidebar-scroll::-webkit-scrollbar-thumb {{ background: #333; border-radius: 2px; }}

  /* ── Niveaux sidebar ── */
  .prod-group  {{ margin-bottom: 2px; }}
  .prod-label  {{
    display: flex; align-items: center; gap: 6px;
    padding: 8px 12px 6px; font-size: 11px; font-weight: 700;
    color: #ccc; text-transform: uppercase; letter-spacing: 1px;
    border-top: 1px solid #222; margin-top: 4px; cursor: pointer;
    user-select: none; transition: background .15s;
  }}
  .prod-label:hover {{ background: #181818; }}
  .prod-children {{ padding-left: 8px; }}

  .seq-group  {{ margin: 1px 0; }}
  .seq-label  {{
    display: flex; align-items: center; gap: 6px;
    padding: 5px 10px; font-size: 11px; font-weight: 600;
    color: #888; cursor: pointer; user-select: none;
    border-radius: 4px; transition: background .15s;
  }}
  .seq-label:hover {{ background: #1a1a1a; color: #aaa; }}
  .seq-children {{ padding-left: 10px; }}

  .shot-group {{ margin: 1px 0; }}
  .shot-label {{
    display: flex; align-items: center; gap: 6px;
    padding: 4px 10px; font-size: 11px; color: #666;
    cursor: pointer; user-select: none; border-radius: 4px;
    transition: background .15s;
  }}
  .shot-label:hover {{ background: #1a1a1a; color: #999; }}
  .shot-children {{ padding-left: 10px; }}

  .layer-group {{ margin: 1px 0; }}
  .layer-label {{
    display: flex; align-items: center; gap: 6px;
    padding: 5px 8px; border-radius: 5px; cursor: pointer;
    font-size: 12px; user-select: none; transition: background .15s;
  }}
  .layer-label:hover {{ background: #1e1e1e; }}
  .lbl-shot {{ color: #888; font-weight: 600; }}
  .lbl-layer {{
    background: #1e2e3e; color: #5ba3f5; font-size: 11px;
    padding: 1px 7px; border-radius: 3px; font-weight: 600;
  }}
  .arrow {{ font-size: 9px; color: #333; transition: transform .2s; min-width: 10px; flex-shrink:0; }}
  .arrow.open {{ transform: rotate(90deg); color: #666; }}
  .run-count {{
    margin-left: auto; background: #1e1e1e; color: #555;
    font-size: 10px; padding: 1px 6px; border-radius: 10px;
  }}
  .run-list {{ padding: 2px 0 4px 16px; }}
  .run-item {{
    padding: 4px 10px; border-radius: 4px; cursor: pointer;
    font-size: 11px; color: #555; font-family: monospace;
    transition: background .1s, color .1s;
  }}
  .run-item:hover {{ background: #1e1e1e; color: #999; }}
  .run-item.active {{ background: #1a2a3a; color: #5ba3f5; }}
  .tag-latest {{
    font-size: 9px; background: #1e3a1e; color: #4a9;
    padding: 1px 5px; border-radius: 3px; margin-left: 4px;
    font-family: sans-serif; vertical-align: middle;
  }}
  .tag-asset {{
    font-size: 9px; background: #3a2a1e; color: #c87a3a;
    padding: 1px 5px; border-radius: 3px; margin-right: 4px;
    font-family: sans-serif; vertical-align: middle;
  }}

  #main {{ flex: 1; display: flex; flex-direction: column; overflow: hidden; }}
  #toolbar {{
    display: flex; align-items: center; gap: 10px;
    padding: 8px 14px; background: #111;
    border-bottom: 1px solid #222; min-height: 38px;
  }}
  #current-label {{ font-size: 12px; color: #555; flex: 1; font-family: monospace; }}
  #open-btn {{
    font-size: 11px; padding: 4px 10px; background: #1e3a1e;
    color: #4a9; border: 1px solid #2a5a2a; border-radius: 4px;
    cursor: pointer; text-decoration: none;
  }}
  #open-btn:hover {{ background: #254a25; }}
  #exr-btn {{
    font-size: 11px; padding: 4px 10px; background: #1a2a3a;
    color: #6af; border: 1px solid #2a4a6a; border-radius: 4px;
    cursor: pointer; font-family: inherit;
  }}
  #exr-btn:hover {{ background: #1e3550; }}
  #exr-btn.copied {{ background: #1a3a1a; color: #4a9; border-color: #2a5a2a; }}
  #report-frame {{ flex: 1; border: none; background: #1a1a1a; }}
  #empty-state {{
    flex: 1; display: flex; align-items: center; justify-content: center;
    color: #333; font-size: 14px;
  }}
</style>
</head>
<body>

<div id="sidebar">
  <div id="sidebar-header">
    <h1>EXR Analyzer — Library</h1>
    <div class="meta">{total} rapport(s) · {now}</div>
  </div>
  <div id="sidebar-search">
    <input type="text" id="search-input" placeholder="Filtrer prod / seq / shot / layer…" oninput="filterSidebar(this.value)">
  </div>
  <div id="sidebar-scroll">
    {sidebar_html}
  </div>
</div>

<div id="main">
  <div id="toolbar">
    <div id="current-label">Sélectionner un rapport</div>
    <button id="exr-btn" onclick="copyExrPath()" style="display:none">📂 Copier chemin EXR</button>
    <a id="open-btn" href="#" target="_blank" style="display:none">Ouvrir ↗</a>
  </div>
  {'<iframe id="report-frame" src="' + escape(default_src) + '"></iframe>' if default_src else '<div id="empty-state">Aucun rapport disponible.</div>'}
</div>

<script>
  const frame   = document.getElementById('report-frame');
  const label   = document.getElementById('current-label');
  const openBtn = document.getElementById('open-btn');
  const exrBtn  = document.getElementById('exr-btn');
  let   currentExrPath = '';

  function loadReport(file, el) {{
    document.querySelectorAll('.run-item.active').forEach(e => e.classList.remove('active'));
    if (el) el.classList.add('active');
    if (frame) frame.src = file;
    label.textContent = file;
    openBtn.href = file;
    openBtn.style.display = '';
    currentExrPath = el ? el.getAttribute('data-exr') : '';
    exrBtn.style.display = currentExrPath ? '' : 'none';
    exrBtn.textContent = '📂 Copier chemin EXR';
    exrBtn.classList.remove('copied');
  }}

  function copyExrPath() {{
    if (!currentExrPath) return;
    navigator.clipboard.writeText(currentExrPath).then(() => {{
      exrBtn.textContent = '✓ Copié !';
      exrBtn.classList.add('copied');
      setTimeout(() => {{
        exrBtn.textContent = '📂 Copier chemin EXR';
        exrBtn.classList.remove('copied');
      }}, 2000);
    }});
  }}

  function toggleSection(id) {{
    const el  = document.getElementById(id);
    const arr = document.getElementById('arr-' + id);
    if (!el) return;
    const open = el.style.display === 'none';
    el.style.display  = open ? '' : 'none';
    if (arr) arr.classList.toggle('open', open);
  }}

  function toggleLayer(id) {{
    const list = document.getElementById('rl-' + id);
    const arr  = document.getElementById('arr-' + id);
    if (!list) return;
    const open = list.style.display === 'none';
    list.style.display = open ? '' : 'none';
    if (arr) arr.classList.toggle('open', open);
  }}

  function filterSidebar(q) {{
    q = q.toLowerCase();
    document.querySelectorAll('.layer-group').forEach(lg => {{
      lg.style.display = (!q || lg.textContent.toLowerCase().includes(q)) ? '' : 'none';
    }});
    document.querySelectorAll('.shot-group').forEach(sg => {{
      const vis = [...sg.querySelectorAll('.layer-group')].some(lg => lg.style.display !== 'none');
      sg.style.display = vis ? '' : 'none';
    }});
    document.querySelectorAll('.seq-group').forEach(sg => {{
      const vis = [...sg.querySelectorAll('.shot-group')].some(sg2 => sg2.style.display !== 'none');
      sg.style.display = vis ? '' : 'none';
    }});
    document.querySelectorAll('.prod-group').forEach(pg => {{
      const vis = [...pg.querySelectorAll('.seq-group')].some(sg => sg.style.display !== 'none');
      pg.style.display = vis ? '' : 'none';
    }});
    if (q) {{
      document.querySelectorAll('.prod-children, .seq-children, .shot-children').forEach(c => c.style.display = '');
    }}
  }}

  function openToReport(file) {{
    const el = document.querySelector(`.run-item[data-file="${{file}}"]`);
    if (!el) return false;
    // Expand all collapsed ancestors
    let node = el.parentElement;
    while (node) {{
      if (node.style && node.style.display === 'none') {{
        node.style.display = '';
        const m = node.id && node.id.match(/^(p|s|sh|rl)-.+/);
        if (m) {{
          const arrId = 'arr-' + node.id.replace(/^rl-/, '');
          const arr = document.getElementById(arrId);
          if (arr) arr.classList.add('open');
        }}
      }}
      node = node.parentElement;
    }}
    loadReport(file, el);
    el.scrollIntoView({{behavior:'smooth', block:'nearest'}});
    return true;
  }}

  // Hash ou premier rapport au chargement
  const hashFile = decodeURIComponent(window.location.hash.slice(1));
  let opened = false;
  if (hashFile) opened = openToReport(hashFile);

  if (!opened) {{
    const firstProd = document.querySelector('.prod-children');
    if (firstProd) {{ firstProd.style.display = ''; document.querySelector('[id^="arr-p-"]').classList.add('open'); }}
    const firstSeq  = document.querySelector('.seq-children');
    if (firstSeq)  {{ firstSeq.style.display  = ''; document.querySelector('[id^="arr-s-"]').classList.add('open'); }}
    const firstShot = document.querySelector('.shot-children');
    if (firstShot) {{ firstShot.style.display = ''; document.querySelector('[id^="arr-sh-"]').classList.add('open'); }}
    const firstLayer = document.querySelector('.layer-label');
    if (firstLayer) {{
      const id = firstLayer.closest('.layer-group').id.replace('lg-', '');
      toggleLayer(id);
      const firstRun = document.querySelector('.run-list .run-item');
      if (firstRun) firstRun.classList.add('active');
    }}
    if (frame && frame.getAttribute('src')) {{
      label.textContent = frame.getAttribute('src');
      openBtn.href = frame.getAttribute('src');
      openBtn.style.display = '';
    }}
  }}
</script>
</body>
</html>
"""

    index_path = reports_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path


# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="EXR Analyzer wrapper")
    parser.add_argument("path",          help="Fichier EXR ou dossier contenant la séquence")
    parser.add_argument("--reports-dir", default=None, help="Dossier racine des rapports (défaut: ./reports/)")
    parser.add_argument("--log-dir",     default=None, help="Dossier pour les logs (optionnel)")
    parser.add_argument("--job-name",    default=None, help="Nom du job Deadline (optionnel, pour le log)")
    parser.add_argument("--open-html",   action="store_true", help="Ouvrir le rapport HTML dans le navigateur une fois terminé")
    args = parser.parse_args()

    input_path = Path(args.path)
    script_dir = Path(__file__).parent

    if not input_path.exists():
        print(f"[ERREUR] Chemin introuvable : {input_path}")
        sys.exit(1)

    info         = parse_path_info(input_path)
    analyze_path = build_glob(input_path)
    ts           = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    label        = info["prefix"]

    reports_dir = Path(args.reports_dir) if args.reports_dir else script_dir / "reports"
    jobs_dir    = reports_dir / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    html_out = jobs_dir / f"{label}_{ts}.html"

    # ── Redirection vers log si --log-dir fourni ──────────────────────
    log_fh = None
    if args.log_dir:
        log_dir = Path(args.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_name = f"{label}_{ts}.log"
        log_path = log_dir / log_name
        log_fh   = open(log_path, "w", encoding="utf-8", buffering=1)
        sys.stdout = log_fh
        sys.stderr = log_fh

    try:
        if args.job_name:
            print(f"  Job     : {args.job_name}")
        print(f"  Prod    : {info.get('prod', 'UNKNOWN')}")
        print(f"  Type    : {info['type']}")
        print(f"  Seq     : {info.get('seq', info.get('group', 'UNKNOWN'))}")
        print(f"  Shot    : {info.get('shot', info.get('sub', 'UNKNOWN'))}")
        print(f"  Layer   : {info.get('layer', info.get('label', 'UNKNOWN'))}")
        print(f"  Analyse : {analyze_path}")
        print(f"  Rapport : {html_out}")
        print(f"\n  Analyse en cours...\n")

        import time as _time
        _t0 = _time.perf_counter()

        analyzer = script_dir / "exr_analyzer" / "exr_analyzer.py"
        analyzer_cmd = [sys.executable, str(analyzer), analyze_path, "--html", str(html_out)]
        if not args.open_html:
            analyzer_cmd.append("--no-browser")
        result   = subprocess.run(
            analyzer_cmd,
            stdout=log_fh or sys.stdout,
            stderr=log_fh or sys.stderr,
            check=False,
        )

        _elapsed = _time.perf_counter() - _t0
        _m, _s   = divmod(int(_elapsed), 60)
        _dur     = f"{_m}m{_s:02d}s" if _m else f"{_s}s"
        print(f"  Duree   : {_dur}")
        print()
        ok      = result.returncode == 0
        prod    = info.get("prod",  "")
        seq     = info.get("seq",   info.get("group", ""))
        shot    = info.get("shot",  info.get("sub",   ""))
        layer   = info.get("layer", info.get("label", ""))
        context = "  ·  ".join(filter(None, [prod, seq, shot, layer]))

        if ok:
            print("  [OK] Analyse terminee - aucune anomalie detectee.")
            send_notification(
                "EXR Analyzer — Termine",
                context,
                "Aucune anomalie detectee",
            )
        else:
            print("  [ATTENTION] Des frames problematiques ont ete detectees.")
            send_notification(
                "EXR Analyzer — Attention",
                context,
                "Des frames problematiques ont ete detectees",
            )

        print(f"\n  Rapport : {html_out}")

        if html_out.exists():
            write_manifest(html_out, info, ts, exr_path=str(input_path))

        index = generate_library(reports_dir)
        print(f"  Library : {index}\n")

        if args.open_html:
            import webbrowser as _wb
            index_html = reports_dir / "index.html"
            if index_html.exists():
                url = "file:///" + index_html.as_posix() + "#" + html_out.name
                _wb.open(url)

    finally:
        if log_fh:
            log_fh.close()
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
