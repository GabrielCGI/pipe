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

# Liste de callbacks Prism que ce plugin tente d'enregistrer.
# On en couvre plusieurs pour etre sur d'attraper le clic droit dans le Media
# Browser quelque soit la version de Prism.
_CALLBACKS = (
    "mediaPlayerContextMenuRequested",
    "openPBListContextMenu",
    "openPBFileContextMenu",
    "productSelectorContextMenuRequested",
    "mediaBrowserContextMenuRequested",
)


class Prism_ExrAnalyzer:

    def __init__(self, core):
        self.core = core
        self.version = "v0.2.0"

        for cb_name in _CALLBACKS:
            try:
                self.core.callbacks.registerCallback(
                    cb_name,
                    self._make_handler(cb_name),
                    plugin=self,
                )
            except Exception:
                pass

    # ── Wrapping callback ───────────────────────────────────────────────────

    def _make_handler(self, cb_name):
        """Genere un handler qui retient le nom du callback declenche."""
        def handler(*args, **kwargs):
            try:
                self._on_context_menu(cb_name, args, kwargs)
            except Exception:
                try:
                    self.core.popup(
                        f"EXR Analyzer plugin error in {cb_name}:\n"
                        f"{traceback.format_exc()}"
                    )
                except Exception:
                    pass
        return handler

    def _on_context_menu(self, cb_name, args, kwargs):
        """Ajoute l'action sans tenter de resoudre le chemin maintenant.
        La resolution se fait au clic — comme ca on voit toujours le menu."""
        rcmenu = None
        if len(args) >= 2 and self._looks_like_menu(args[1]):
            rcmenu = args[1]
        else:
            for a in args:
                if self._looks_like_menu(a):
                    rcmenu = a
                    break

        if rcmenu is None:
            return

        origin = args[0] if len(args) >= 1 else None

        action = rcmenu.addAction("Analyser la sequence EXR...")
        action.triggered.connect(
            lambda checked=False, o=origin, a=args, k=kwargs:
                self._on_click(cb_name, o, a, k)
        )

    @staticmethod
    def _looks_like_menu(obj) -> bool:
        return obj is not None and hasattr(obj, "addAction") and callable(getattr(obj, "addAction"))

    # ── Click ───────────────────────────────────────────────────────────────

    def _on_click(self, cb_name, origin, args, kwargs):
        try:
            seq_dir, debug_info = self._extract_sequence_dir(origin, args, kwargs)
            if seq_dir is None:
                self.core.popup(
                    "EXR Analyzer\n\n"
                    f"Impossible de trouver le dossier de la sequence.\n\n"
                    f"Callback : {cb_name}\n"
                    f"Pistes essayees :\n{debug_info}"
                )
                return
            self._launch(seq_dir)
        except Exception:
            self.core.popup(f"EXR Analyzer error:\n{traceback.format_exc()}")

    # ── Resolution du dossier de la sequence ────────────────────────────────

    def _extract_sequence_dir(self, origin, args, kwargs):
        """Tente plusieurs strategies. Retourne (path|None, debug_text)."""
        candidates = []
        debug = []

        # 1) args et kwargs : strings directes ou objets a attributs
        for src_name, src in (("args", args), ("kwargs", list(kwargs.values()))):
            for i, x in enumerate(src):
                if isinstance(x, str):
                    candidates.append((f"{src_name}[{i}] str", x))
                else:
                    for attr in ("path", "filePath", "file_path", "filepath"):
                        val = getattr(x, attr, None)
                        if isinstance(val, str):
                            candidates.append((f"{src_name}[{i}].{attr}", val))

        # 2) origin Prism : methodes courantes du Media Browser
        if origin is not None:
            for meth in (
                "getCurrentRenderingVersion",
                "getCurRenderVersion",
                "getCurrentVersion",
                "getSelectedMediaVersion",
                "getCurrentMedia",
                "getCurrentSequence",
                "getSelectedFiles",
                "getSelected",
            ):
                fn = getattr(origin, meth, None)
                if callable(fn):
                    try:
                        result = fn()
                    except Exception as e:
                        debug.append(f"  origin.{meth}() raised {type(e).__name__}")
                        continue
                    if isinstance(result, str):
                        candidates.append((f"origin.{meth}()", result))
                    elif isinstance(result, (list, tuple)):
                        for j, item in enumerate(result):
                            if isinstance(item, str):
                                candidates.append((f"origin.{meth}()[{j}] str", item))
                            else:
                                for attr in ("path", "filePath"):
                                    val = getattr(item, attr, None)
                                    if isinstance(val, str):
                                        candidates.append((f"origin.{meth}()[{j}].{attr}", val))
                    elif result is not None:
                        for attr in ("path", "filePath"):
                            val = getattr(result, attr, None)
                            if isinstance(val, str):
                                candidates.append((f"origin.{meth}().{attr}", val))

        # 3) Filtre : on garde le premier qui pointe vers un dossier d'EXR
        for src, c in candidates:
            d = self._resolve_to_exr_dir(c)
            if d is not None:
                return d, ""
            debug.append(f"  {src} = {c!r}  ->  pas un .exr / dossier d'exr")

        if not candidates:
            debug.append("  (aucun candidat trouve dans args/kwargs/origin)")
        return None, "\n".join(debug)

    @staticmethod
    def _resolve_to_exr_dir(path: str):
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
