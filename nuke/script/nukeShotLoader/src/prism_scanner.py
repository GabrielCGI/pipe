"""
Prism Project Scanner
Scans Prism project structure to extract sequences, shots, and frame ranges.
Adapted from nukeMultiShotSetup prism_extractor.py
"""

import os
import json
from typing import Dict, Optional, Tuple
from .config import Config


class PrismScanner:
    """Scanner for Prism project structure"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or Config.DEFAULT_PROJECT_ROOT
        self.shots_path = os.path.join(self.project_root, Config.SHOTS_PATH)
        self.pipeline_path = os.path.join(self.project_root, Config.PIPELINE_PATH)

        self._cache = {}

    def get_shot_frame_range(self, sequence: str, shot: str) -> Optional[Tuple[int, int]]:
        """
        Get frame range for a shot from shotInfo.json.

        Args:
            sequence (str): Sequence name
            shot (str): Shot name

        Returns:
            Optional[Tuple[int, int]]: (first_frame, last_frame) or None if not found
        """
        cache_key = f"{sequence}_{shot}_framerange"

        # Check cache
        if Config.ENABLE_CACHE and cache_key in self._cache:
            return self._cache[cache_key]

        shotinfo_path = os.path.join(self.pipeline_path, Config.SHOTINFO_JSON)

        if not os.path.exists(shotinfo_path):
            print(f"[PrismScanner] shotInfo.json not found: {shotinfo_path}")
            return None

        try:
            with open(shotinfo_path, 'r') as f:
                shotinfo = json.load(f)

            # Navigate through JSON structure
            # Expected structure: {"sequences": {"SEQ_name": {"shots": {"SH_name": {"frameStart": X, "frameEnd": Y}}}}}
            sequences = shotinfo.get("sequences", {})
            seq_data = sequences.get(sequence, {})
            shots = seq_data.get("shots", {})
            shot_data = shots.get(shot, {})

            frame_start = shot_data.get("frameStart")
            frame_end = shot_data.get("frameEnd")

            if frame_start is not None and frame_end is not None:
                result = (int(frame_start), int(frame_end))
                self._cache[cache_key] = result
                print(f"[PrismScanner] Frame range for {sequence}/{shot}: {result}")
                return result
            else:
                print(f"[PrismScanner] Frame range not found for {sequence}/{shot}")
                return None

        except Exception as e:
            print(f"[PrismScanner] Error reading frame range for {sequence}/{shot}: {e}")
            return None

    def get_project_info(self) -> Dict:
        """
        Extract basic project information from pipeline.json.

        Returns:
            Dict: Project info (name, fps, resolution, etc.)
        """
        pipeline_json_path = os.path.join(self.pipeline_path, Config.PIPELINE_JSON)

        if not os.path.exists(pipeline_json_path):
            print(f"[PrismScanner] pipeline.json not found: {pipeline_json_path}")
            return {
                "name": os.path.basename(self.project_root),
                "path": self.project_root,
                "fps": "25.0",
                "width": 1920,
                "height": 1080
            }

        try:
            with open(pipeline_json_path, 'r') as f:
                data = json.load(f)

            globals_data = data.get("globals", {})

            project_info = {
                "name": globals_data.get("project_name", os.path.basename(self.project_root)),
                "path": self.project_root,
                "fps": str(globals_data.get("fps", 25.0)),
                "width": globals_data.get("resolution_width", 1920),
                "height": globals_data.get("resolution_height", 1080)
            }

            print(f"[PrismScanner] Project info: {project_info}")
            return project_info

        except Exception as e:
            print(f"[PrismScanner] Error reading project info: {e}")
            return {
                "name": os.path.basename(self.project_root),
                "path": self.project_root,
                "fps": "25.0",
                "width": 1920,
                "height": 1080
            }
