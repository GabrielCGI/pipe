"""
Prism 2.x plugin — EXR Analyzer.

INSTALLATION :
  Prism User Settings > Plugins > drag-and-drop ce fichier dans la liste.
  (Ou place-le dans ton dossier custom plugins Prism et reload.)

Ajoute "Analyser la sequence EXR..." dans le menu clic-droit du Media Browser.
"""
from __future__ import annotations

import os
import sys
import subprocess
import datetime
import traceback


# ── Constantes (alignees avec le tool live) ─────────────────────────────────
TOOL_ROOT   = r"R:\pipeline\pipe\deadline\exr_analyzer"
REPORTS_DIR = r"R:\pipeline\pipe\deadline\exr_analyzer\reports"
LOGS_DIR    = r"R:\devToto\Claude\exr-analyzer\logs-deadline"
PYTHON_EXE  = r"C:\Program Files\Thinkbox\Deadline10\bin\python3\python.exe"
SITE_PKG    = r"R:\pipeline\networkInstall\python_shares\python310_deadline_discord_pkgs\Lib\site-packages"


class Prism_ExrAnalyzer:

    def __init__(self, core):
        self.core = core
        self.version = "v0.1.0"

        # Plusieurs callbacks pour couvrir Media Browser ET Project Browser.
        # Si Prism n'a pas l'un d'eux, registerCallback echoue silencieusement
        # ou on l'enrobe try/except.
        for cb_name in (
            "mediaPlayerContextMenuRequested",
            "openPBListContextMenu",
            "openPBFileContextMenu",
        ):
            try:
                self.core.callbacks.registerCallback(
                    cb_name,
                    self._on_context_menu,
                    plugin=self,
                )
            except Exception:
                pass

    # ── Callback ────────────────────────────────────────────────────────────

    def _on_context_menu(self, *args, **kwargs):
        """Generique : on essaye d'extraire un chemin de folder de la signature.

        Les callbacks Prism passent (origin, rcmenu, ...) avec ensuite des args
        variables : un filePath, ou un objet version, ou un widget item.
        On tape un peu dans le tas pour trouver un dossier qui contient des EXR.
        """
        try:
            origin = args[0] if len(args) > 0 else None
            rcmenu = args[1] if len(args) > 1 else None

            if rcmenu is None:
                return

            seq_dir = self._extract_sequence_dir(origin, args[2:])
            if seq_dir is None:
                return

            action = rcmenu.addAction("Analyser la sequence EXR...")
            action.triggered.connect(lambda: self._launch(seq_dir))
        except Exception:
            # Jamais bloquer le menu Prism a cause d'une erreur de plugin
            pass

    # ── Resolution du dossier de la sequence ────────────────────────────────

    def _extract_sequence_dir(self, origin, extras) -> str | None:
        """Tente plusieurs strategies pour trouver le dossier d'une sequence EXR."""
        candidates = []

        # 1) args supplementaires : filePath string ou objet ayant .path
        for x in extras:
            if isinstance(x, str):
                candidates.append(x)
            else:
                for attr in ("path", "filePath", "file_path"):
                    val = getattr(x, attr, None)
                    if isinstance(val, str):
                        candidates.append(val)

        # 2) origin Prism : on tente quelques methodes courantes du Media Browser
        if origin is not None:
            for meth in (
                "getCurrentRenderingVersion",
                "getCurRenderVersion",
                "getSelectedMediaVersion",
                "getCurrentMedia",
            ):
                fn = getattr(origin, meth, None)
                if callable(fn):
                    try:
                        result = fn()
                        if isinstance(result, str):
                            candidates.append(result)
                        elif result is not None:
                            for attr in ("path", "filePath"):
                                val = getattr(result, attr, None)
                                if isinstance(val, str):
                                    candidates.append(val)
                    except Exception:
                        pass

        # 3) Filtre : on garde le premier qui pointe vers un dossier d'EXR
        for c in candidates:
            d = self._resolve_to_exr_dir(c)
            if d is not None:
                return d
        return None

    @staticmethod
    def _resolve_to_exr_dir(path: str) -> str | None:
        """Si path est un .exr, retourne le parent. Si dossier contenant des
        .exr, retourne path. Sinon None."""
        if not isinstance(path, str) or not path:
            return None
        try:
            if os.path.isfile(path) and path.lower().endswith(".exr"):
                return os.path.dirname(path)
            if os.path.isdir(path):
                for f in os.listdir(path):
                    if f.lower().endswith(".exr"):
                        return path
        except Exception:
            return None
        return None

    # ── Lancement ───────────────────────────────────────────────────────────

    def _launch(self, seq_dir: str) -> None:
        """Lance analyze_exr.py en arriere-plan, mode metadata-only par defaut."""
        try:
            analyze_script = os.path.join(TOOL_ROOT, "analyze_exr.py")

            os.makedirs(LOGS_DIR, exist_ok=True)
            ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = os.path.join(LOGS_DIR, f"prism_{ts}.log")
            log_fh   = open(log_path, "w", encoding="utf-8", buffering=1)
            machine  = os.environ.get("COMPUTERNAME", "unknown")
            user     = os.environ.get("USERNAME",     "unknown")
            log_fh.write(f"[{ts}] EXR Analyzer (Prism) lance\n")
            log_fh.write(f"  machine    : {machine}\n")
            log_fh.write(f"  user       : {user}\n")
            log_fh.write(f"  output_dir : {seq_dir}\n")
            log_fh.write(f"  python     : {PYTHON_EXE}\n")
            log_fh.write(f"  script     : {analyze_script}\n\n")
            log_fh.flush()

            env = dict(os.environ)
            existing_pp = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = SITE_PKG + os.pathsep + existing_pp if existing_pp else SITE_PKG

            cmd = [
                PYTHON_EXE,
                analyze_script,
                seq_dir,
                "--reports-dir",   REPORTS_DIR,
                "--log-dir",       LOGS_DIR,
                "--metadata-only",
                "--open-html",
            ]

            subprocess.Popen(
                cmd,
                env=env,
                stdout=log_fh,
                stderr=log_fh,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )

            self.core.popup(
                f"EXR Analyzer\nAnalyse lancee en arriere-plan.\n\n{seq_dir}",
                title="EXR Analyzer",
            )
        except Exception:
            self.core.popup(f"EXR Analyzer error:\n{traceback.format_exc()}")
