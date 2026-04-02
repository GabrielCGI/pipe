"""
ui/main_window.py — Main application window.

Layout:
    Left pane  : ProjectPanel | StepPanel | VersionPanel
    Right pane : ShotPanel | OutputPanel | LogPanel
    Bottom bar : Generate button

All filesystem I/O runs in a ScanWorker QThread to keep the UI responsive.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QThread, Signal, Slot, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from config import APP_NAME, APP_VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, RV_EXECUTABLE, HIERO_EXECUTABLE
from core.builder import ShotMedia, TimelineBuilder
from core.project import PrismProject
from core.scanner import ProjectScanner, ShotEntry
from ui.log_panel import LogPanel
from ui.output_panel import OutputPanel
from ui.project_panel import ProjectPanel
from ui.shot_panel import ShotPanel
from ui.step_panel import StepPanel
from ui.version_panel import VersionPanel


# ---------------------------------------------------------------------------
# Background worker — runs scan + media resolution off the main thread
# ---------------------------------------------------------------------------

class ScanWorker(QThread):
    """
    Scans shots and resolves media versions in a background thread.
    Signals are emitted progressively so the UI can update live.
    """

    shot_scanned = Signal(object, str, bool)   # (ShotEntry, status_text, ok)
    scan_complete = Signal(list)               # list[ShotMedia]
    scan_error = Signal(str)

    def __init__(
        self,
        project: PrismProject,
        shots: List[ShotEntry],
        tasks: List[str],
        version_overrides: Dict[str, Dict[str, Optional[str]]],
        fps: float,
    ) -> None:
        super().__init__()
        self.project = project
        self.shots = shots
        self.tasks = tasks
        self.version_overrides = version_overrides  # full_name -> task -> version_str or None
        self.fps = fps
        self._abort = False

    def abort(self) -> None:
        self._abort = True

    def run(self) -> None:
        try:
            self._do_scan()
        except Exception as exc:
            self.scan_error.emit(str(exc))

    # Fallback pipeline steps tried when the requested task has no versions.
    # Ordered from most to least preferred. Lighting is intentionally excluded
    # because it is typically rendered as separate layers and does not represent
    # the composited result.
    _FALLBACK_ORDER = [
        "Compo", "MattePaint", "FX", "Simulation", "Anim", "Animation", "Layout",
    ]

    def _do_scan(self) -> None:
        scanner = ProjectScanner(self.project)
        result: List[ShotMedia] = []

        # Scan requested tasks AND fallback candidates in one pass per shot
        all_tasks_to_scan = list(dict.fromkeys(self.tasks + self._FALLBACK_ORDER))

        for shot in self.shots:
            if self._abort:
                return

            # Scan versions for this shot (requested + fallback candidates)
            scanner.scan_versions_for_shot(shot, all_tasks_to_scan)

            for task in self.tasks:
                if self._abort:
                    return

                overrides = self.version_overrides.get(shot.full_name, {})
                pinned_version = overrides.get(task)  # None = use latest

                # Find the target version
                versions = shot.versions_by_task.get(task, [])
                if not versions:
                    # No versions for requested task — try fallback steps
                    fallback_media = None
                    fallback_task = None
                    fallback_version_entry = None
                    for fb_task in self._FALLBACK_ORDER:
                        if fb_task == task:
                            continue
                        fb_versions = shot.versions_by_task.get(fb_task, [])
                        if not fb_versions:
                            continue
                        fb_entry = fb_versions[-1]
                        fb_media = scanner.find_media(
                            fb_entry,
                            fps=self.fps,
                            fallback_frame_range=shot.frame_range,
                        )
                        if fb_media:
                            fallback_media = fb_media
                            fallback_task = fb_task
                            fallback_version_entry = fb_entry
                            break

                    if fallback_media:
                        status = (
                            f"{task}: no versions"
                            f" → using {fallback_task}"
                            f" {fallback_version_entry.version_str}"
                        )
                        self.shot_scanned.emit(shot, status, False)
                        result.append(ShotMedia(
                            shot=shot,
                            task=task,
                            media=fallback_media,
                            version_str=f"[{fallback_task}] {fallback_version_entry.version_str}",
                        ))
                    else:
                        status = f"{task}: no versions"
                        self.shot_scanned.emit(shot, status, False)
                        result.append(ShotMedia(shot=shot, task=task, media=None, version_str="—"))
                    continue

                # Select pinned or latest
                if pinned_version:
                    version_entry = next(
                        (v for v in versions if v.version_str == pinned_version), versions[-1]
                    )
                else:
                    version_entry = versions[-1]  # latest

                # Resolve media
                media = scanner.find_media(
                    version_entry,
                    fps=self.fps,
                    fallback_frame_range=shot.frame_range,
                )

                if media:
                    status = f"{task}: {version_entry.version_str} OK"
                    self.shot_scanned.emit(shot, status, True)
                else:
                    status = f"{task}: {version_entry.version_str} no media"
                    self.shot_scanned.emit(shot, status, False)

                result.append(ShotMedia(
                    shot=shot,
                    task=task,
                    media=media,
                    version_str=version_entry.version_str,
                ))

        self.scan_complete.emit(result)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self._project: Optional[PrismProject] = None
        self._shots: List[ShotEntry] = []
        self._worker: Optional[ScanWorker] = None
        self._last_results: List[ShotMedia] = []
        self._default_output_path: Optional[Path] = None
        self._open_rv_after_scan: bool = False     # set True when "Generate & Open in RV" triggers a scan
        self._open_hiero_after_scan: bool = False  # set True when "Generate & Open in Hiero" triggers a scan

        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(8, 8, 8, 4)

        splitter = QSplitter(Qt.Horizontal)

        # ---- Left pane ------------------------------------------------
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.project_panel = ProjectPanel()
        self.step_panel = StepPanel()
        self.version_panel = VersionPanel()

        self.step_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.version_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        left_layout.addWidget(self.project_panel)
        left_layout.addWidget(self.step_panel)
        left_layout.addWidget(self.version_panel)

        # ---- Right pane -----------------------------------------------
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.shot_panel = ShotPanel()
        self.output_panel = OutputPanel()
        self.log_panel = LogPanel()

        self.shot_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.log_panel.setMaximumHeight(180)

        right_layout.addWidget(self.shot_panel)
        right_layout.addWidget(self.output_panel)
        right_layout.addWidget(self.log_panel)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        root_layout.addWidget(splitter)

        # ---- Bottom bar -----------------------------------------------
        bottom_row = QHBoxLayout()
        self._scan_btn = QPushButton("Scan && Preview")
        self._scan_btn.setEnabled(False)
        self._generate_btn = QPushButton("Generate OTIO")
        self._generate_btn.setEnabled(False)
        self._generate_btn.setStyleSheet(
            "QPushButton { background: #2f80ed; color: white; font-weight: bold; "
            "padding: 6px 18px; border-radius: 4px; }"
            "QPushButton:disabled { background: #555; color: #888; }"
        )
        self._generate_rv_btn = QPushButton("Generate && Open in RV")
        self._generate_rv_btn.setEnabled(False)
        self._generate_rv_btn.setStyleSheet(
            "QPushButton { background: #6c3483; color: white; font-weight: bold; "
            "padding: 6px 18px; border-radius: 4px; }"
            "QPushButton:disabled { background: #555; color: #888; }"
        )
        self._generate_hiero_btn = QPushButton("Generate && Open in Hiero")
        self._generate_hiero_btn.setEnabled(False)
        self._generate_hiero_btn.setStyleSheet(
            "QPushButton { background: #1a6b4a; color: white; font-weight: bold; "
            "padding: 6px 18px; border-radius: 4px; }"
            "QPushButton:disabled { background: #555; color: #888; }"
        )
        bottom_row.addWidget(self._scan_btn)
        bottom_row.addStretch()
        bottom_row.addWidget(self._generate_btn)
        bottom_row.addWidget(self._generate_rv_btn)
        bottom_row.addWidget(self._generate_hiero_btn)
        root_layout.addLayout(bottom_row)

        self.setStatusBar(QStatusBar())

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self.project_panel.project_loaded.connect(self._on_project_loaded)
        self.project_panel.project_error.connect(self._on_project_error)
        self.shot_panel.selection_changed.connect(self._on_shot_selection_changed)
        self.step_panel.selection_changed.connect(self._on_step_selection_changed)
        self._scan_btn.clicked.connect(self._on_scan)
        self._generate_btn.clicked.connect(self._on_generate)
        self._generate_rv_btn.clicked.connect(self._on_generate_and_open_rv)
        self._generate_hiero_btn.clicked.connect(self._on_generate_and_open_hiero)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    @Slot(object)
    def _on_project_loaded(self, project: PrismProject) -> None:
        self._project = project
        self.log_panel.info(f"Project loaded: {project.name}  (FPS: {project.fps})")
        self.output_panel.set_fps(project.fps)

        # Populate steps from project
        self.step_panel.populate(project)

        # Scan shots (fast, no media resolution)
        scanner = ProjectScanner(project)
        self._shots = scanner.scan_shots()
        self.shot_panel.populate(self._shots)
        self.log_panel.info(f"Found {len(self._shots)} shots.")
        self._refresh_default_output()

        self._scan_btn.setEnabled(True)
        self._generate_btn.setEnabled(bool(self._shots))
        self._generate_rv_btn.setEnabled(bool(self._shots))
        self._generate_hiero_btn.setEnabled(bool(self._shots))
        self.statusBar().showMessage(f"Project: {project.name} — {len(self._shots)} shots")

    @Slot(str)
    def _on_project_error(self, message: str) -> None:
        self.log_panel.error(message)
        self._scan_btn.setEnabled(False)
        self._generate_btn.setEnabled(False)
        self._generate_rv_btn.setEnabled(False)
        self._generate_hiero_btn.setEnabled(False)

    @Slot(list)
    def _on_shot_selection_changed(self, shots: List[ShotEntry]) -> None:
        tasks = self.step_panel.get_selected_tasks()
        self.version_panel.populate(shots, tasks)

    @Slot(list)
    def _on_step_selection_changed(self, _tasks: List[str]) -> None:
        self._last_results = []  # invalidate scan results when steps change
        self._refresh_default_output()

    def _refresh_default_output(self) -> None:
        """Auto-fill the output path unless the user has set a custom one."""
        if self._project is None:
            return
        tasks = self.step_panel.get_selected_tasks()
        new_default = self._build_default_output_path(self._project, tasks)
        current = self.output_panel.get_output_path()
        if str(current) in (".", "") or current == self._default_output_path:
            self.output_panel.set_output_path(str(new_default))
        self._default_output_path = new_default

    def _build_default_output_path(self, project: PrismProject, tasks: List[str]) -> Path:
        date_str = datetime.now().strftime("%y%m%d")
        tasks_str = "+".join(tasks) if tasks else "timeline"
        base_name = f"{date_str}_{project.name}_{tasks_str}_timeline"
        folder = Path(tempfile.gettempdir())
        version = 1
        while True:
            filename = f"{base_name}_v{version:03d}.otio"
            if not (folder / filename).exists():
                return folder / filename
            version += 1

    def _build_version_overrides(
        self, shots: List[ShotEntry], tasks: List[str]
    ) -> Dict[str, Dict[str, Optional[str]]]:
        return {
            shot.full_name: {
                task: self.version_panel.get_version_for(shot, task)
                for task in tasks
            }
            for shot in shots
        }

    @Slot()
    def _on_scan(self) -> None:
        """Run the background scan to resolve media for selected shots/tasks."""
        if self._project is None:
            return
        shots = self.shot_panel.get_selected_shots()
        tasks = self.step_panel.get_selected_tasks()

        if not shots:
            self.log_panel.warning("No shots selected.")
            return
        if not tasks:
            self.log_panel.warning("No pipeline steps selected.")
            return

        self.log_panel.clear()
        self.log_panel.info(f"Scanning {len(shots)} shots for tasks: {', '.join(tasks)}")
        self._scan_btn.setEnabled(False)
        self._generate_btn.setEnabled(False)
        self._generate_rv_btn.setEnabled(False)
        self._generate_hiero_btn.setEnabled(False)

        self._worker = ScanWorker(
            project=self._project,
            shots=shots,
            tasks=tasks,
            version_overrides=self._build_version_overrides(shots, tasks),
            fps=self.output_panel.get_fps(),
        )
        self._worker.shot_scanned.connect(self._on_shot_scanned)
        self._worker.scan_complete.connect(self._on_scan_complete)
        self._worker.scan_error.connect(self._on_scan_error)
        self._worker.start()

    @Slot(object, str, bool)
    def _on_shot_scanned(self, shot: ShotEntry, status: str, ok: bool) -> None:
        self.shot_panel.update_shot_status(shot, status, ok)
        if ok:
            self.log_panel.success(f"{shot.display_name}: {status}")
        else:
            self.log_panel.warning(f"{shot.display_name}: {status}")

    def _finish_scan(self, results: List[ShotMedia]) -> None:
        self._last_results = results
        ok_count = sum(1 for sm in results if sm.media is not None)
        self.log_panel.info(
            f"Scan complete: {ok_count} clips, {len(results) - ok_count} missing."
        )
        self._update_shot_frame_columns(results)
        self._scan_btn.setEnabled(True)
        self._generate_btn.setEnabled(bool(results))
        self._generate_rv_btn.setEnabled(bool(results))
        self._generate_hiero_btn.setEnabled(bool(results))

    @Slot(list)
    def _on_scan_complete(self, results: List[ShotMedia]) -> None:
        self._finish_scan(results)

    @Slot(list)
    def _on_scan_complete_then_export(self, results: List[ShotMedia]) -> None:
        """Called when a scan triggered by Generate completes — export immediately."""
        self._finish_scan(results)
        if not results:
            return
        if self._open_hiero_after_scan:
            output_paths = self._export_timeline(results, use_file_uri=True, suffix="_hiero")
            if output_paths:
                self._launch_hiero(output_paths)
        else:
            output_paths = self._export_timeline(results)
            if output_paths and self._open_rv_after_scan:
                self._launch_rv(output_paths)

    @Slot(str)
    def _on_scan_error(self, message: str) -> None:
        self.log_panel.error(f"Scan error: {message}")
        self._scan_btn.setEnabled(True)

    @Slot()
    def _on_generate(self) -> None:
        """Build and export one .otio per task, running a scan first if needed."""
        self._open_rv_after_scan = False
        self._open_hiero_after_scan = False
        if not self._last_results:
            self._run_scan_then_export()
        else:
            self._export_timeline(self._last_results)

    @Slot()
    def _on_generate_and_open_rv(self) -> None:
        """Export one .otio per task then open all of them in RV."""
        self._open_rv_after_scan = True
        self._open_hiero_after_scan = False
        if not self._last_results:
            self._run_scan_then_export()
        else:
            output_paths = self._export_timeline(self._last_results)
            if output_paths:
                self._launch_rv(output_paths)

    @Slot()
    def _on_generate_and_open_hiero(self) -> None:
        """Export one .otio per task (with file:/// URIs) then open all of them in Hiero Player."""
        self._open_rv_after_scan = False
        self._open_hiero_after_scan = True
        if not self._last_results:
            self._run_scan_then_export()
        else:
            output_paths = self._export_timeline(
                self._last_results, use_file_uri=True, suffix="_hiero"
            )
            if output_paths:
                self._launch_hiero(output_paths)

    def _run_scan_then_export(self) -> None:
        """Start a scan; export (and optionally open RV) when it completes."""
        if self._project is None:
            return
        shots = self.shot_panel.get_selected_shots()
        tasks = self.step_panel.get_selected_tasks()
        if not shots:
            self.log_panel.warning("No shots selected.")
            return
        if not tasks:
            self.log_panel.warning("No pipeline steps selected.")
            return

        output_path = self.output_panel.get_output_path()
        if not output_path or str(output_path) in (".", ""):
            self.log_panel.error("Please select an output .otio file path.")
            return

        self.log_panel.clear()
        self.log_panel.info(f"Scanning {len(shots)} shots for tasks: {', '.join(tasks)}")
        self._scan_btn.setEnabled(False)
        self._generate_btn.setEnabled(False)
        self._generate_rv_btn.setEnabled(False)
        self._generate_hiero_btn.setEnabled(False)

        self._worker = ScanWorker(
            project=self._project,
            shots=shots,
            tasks=tasks,
            version_overrides=self._build_version_overrides(shots, tasks),
            fps=self.output_panel.get_fps(),
        )
        self._worker.shot_scanned.connect(self._on_shot_scanned)
        self._worker.scan_complete.connect(self._on_scan_complete_then_export)
        self._worker.scan_error.connect(self._on_scan_error)
        self._worker.start()

    def _update_shot_frame_columns(self, results: List[ShotMedia]) -> None:
        """Update the Frames column for each shot using actual media ranges."""
        seen: set = set()
        for sm in results:
            if sm.media is not None and sm.shot.full_name not in seen:
                self.shot_panel.update_shot_frames(
                    sm.shot, sm.media.frame_start, sm.media.frame_end
                )
                seen.add(sm.shot.full_name)

    def _export_timeline(
        self,
        results: List[ShotMedia],
        use_file_uri: bool = False,
        suffix: str = "",
    ) -> List[Path]:
        """Build and export a single .otio file with one track per task. Returns list of written paths."""
        output_base = self.output_panel.get_output_path()
        if not output_base or str(output_base) in (".", ""):
            self.log_panel.error("Please select an output .otio file path.")
            return []

        timeline_name = self.output_panel.get_timeline_name()
        fps = self.output_panel.get_fps()

        base = Path(output_base)
        stem = base.stem    # e.g. "260328_ProjectName_Anim+Compo_timeline_v001"
        parent = base.parent
        output_path = parent / f"{stem}{suffix}.otio"

        try:
            builder = TimelineBuilder(fps=fps, use_file_uri=use_file_uri)
            timeline = builder.build(results, timeline_name=timeline_name)
            TimelineBuilder.export(timeline, output_path)
            self.log_panel.success(f"Exported: {output_path.name}")
            self.statusBar().showMessage(f"Exported timeline to {parent}")
            return [output_path]
        except Exception as exc:
            self.log_panel.error(f"Export failed: {exc}")
            return []

    # Script Python déployé dans ~/.nuke/Python/Startup/ pour auto-importer le .otio
    _HIERO_STARTUP_SCRIPT = textwrap.dedent("""\
        # otio_review_autoload.py — Auto-generated by OTIO Review Tool.
        # Imports a .otio file passed via OTIO_REVIEW_AUTOLOAD env var when launching Hiero.
        # Does nothing if Hiero is launched without that environment variable.
        import os
        import hiero.core
        import hiero.core.events
        from hiero.importers.FnOTIOImporter import OtioImporter

        _OTIO_PATH = os.environ.get("OTIO_REVIEW_AUTOLOAD", "")

        def _do_import(event):
            if not _OTIO_PATH or not os.path.isfile(_OTIO_PATH):
                return
            projects = hiero.core.projects()
            project = projects[0] if projects else hiero.core.newProject()
            OtioImporter().importToNewSequence(_OTIO_PATH, project.clipsBin())

        if _OTIO_PATH:
            hiero.core.events.registerInterest("kStartup", _do_import)
    """)

    def _deploy_hiero_startup_script(self) -> None:
        """Write the auto-load startup script to ~/.nuke/Python/Startup/."""
        startup_dir = Path.home() / ".nuke" / "Python" / "Startup"
        startup_dir.mkdir(parents=True, exist_ok=True)
        script_path = startup_dir / "otio_review_autoload.py"
        script_path.write_text(self._HIERO_STARTUP_SCRIPT, encoding="utf-8")

    def _launch_hiero(self, otio_paths: List[Path]) -> None:
        """Launch Hiero Player (Nuke --player) and auto-import the first .otio file."""
        hiero_exe = Path(HIERO_EXECUTABLE)
        if not hiero_exe.exists():
            self.log_panel.warning(f"Hiero not found at: {hiero_exe}")
            QMessageBox.warning(
                self,
                "Hiero not found",
                f"Could not find Hiero executable:\n{hiero_exe}\n\n"
                "Please open the .otio file(s) manually in Hiero Player.",
            )
            return
        try:
            self._deploy_hiero_startup_script()
            env = os.environ.copy()
            if otio_paths:
                env["OTIO_REVIEW_AUTOLOAD"] = str(otio_paths[0])
            subprocess.Popen(
                [str(hiero_exe), "--player"],
                cwd=tempfile.gettempdir(),
                env=env,
            )
            names = ", ".join(p.name for p in otio_paths)
            self.log_panel.info(f"Launched Hiero Player — auto-loading: {names}")
        except Exception as exc:
            self.log_panel.error(f"Failed to launch Hiero Player: {exc}")

    def _launch_rv(self, otio_paths: List[Path]) -> None:
        """Launch OpenRV with one or more .otio files."""
        rv_exe = Path(RV_EXECUTABLE)
        if not rv_exe.exists():
            self.log_panel.warning(f"RV not found at: {rv_exe}")
            QMessageBox.warning(
                self,
                "RV not found",
                f"Could not find RV executable:\n{rv_exe}\n\n"
                "Please open the .otio file(s) manually in RV.",
            )
            return
        try:
            subprocess.Popen([str(rv_exe)] + [str(p) for p in otio_paths])
            names = ", ".join(p.name for p in otio_paths)
            self.log_panel.info(f"Launched RV with: {names}")
        except Exception as exc:
            self.log_panel.error(f"Failed to launch RV: {exc}")

    def closeEvent(self, event) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.abort()
            self._worker.wait(2000)
        super().closeEvent(event)
