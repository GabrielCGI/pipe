"""Shot context shared by the dialog tabs."""

from typing import Optional

from . import project
from .config import Config
from .prefs import ShotLoaderPrefs


class ShotSession:
    """Project root, current sequence/shot and the project prefs, for the
    script the dialog was opened on."""

    def __init__(self, script_path: Optional[str]):
        self.script_path = script_path
        detected_root = project.detect_project_root(script_path)
        self.project_detected = detected_root is not None
        self.project_root = detected_root or Config.DEFAULT_PROJECT_ROOT
        self.prefs = ShotLoaderPrefs.for_project(detected_root)
        self.sequence: Optional[str] = None
        self.shot: Optional[str] = None

    @property
    def project_name(self) -> str:
        return project.project_name(self.project_root) if self.project_detected else "No Project Found"

    @property
    def has_shot(self) -> bool:
        return bool(self.sequence and self.shot)

    @property
    def shot_key(self) -> str:
        return f"{self.sequence}/{self.shot}"

    def follows(self, script_path: Optional[str]) -> bool:
        """False once the current script belongs to another project or shot
        (another script opened in this Nuke): the dialog must be rebuilt, or
        it would load that shot's assets into this script. A new version of
        the same script (Save Version) keeps the session."""
        if script_path == self.script_path:
            return True
        same = (script_path is not None
                and project.detect_project_root(script_path) == (self.project_root if self.project_detected else None)
                and project.detect_shot_context(script_path) == ((self.sequence, self.shot) if self.has_shot else None))
        if same:
            self.script_path = script_path
        return same
