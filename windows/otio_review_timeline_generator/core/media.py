"""
core/media.py — MediaItem dataclass and MediaDiscovery.

Handles detection of:
  - Prism dot-separated image sequences (output.1001.exr, file.name.0001.exr)
  - Video files (mp4, mov, mxf)

Builds the %04d abstract path expected by OTIO for image sequences.
"""

from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import (
    IMAGE_SEQ_EXTENSIONS,
    VIDEO_EXTENSIONS,
    FRAME_PATTERN,
    DEFAULT_FPS,
)


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------

@dataclass
class MediaItem:
    """All information needed to create an OTIO ExternalReference."""
    path: Path                   # Concrete first-frame path (seq) or video path
    media_type: str              # "image_sequence" or "video"
    frame_start: int             # First frame number (e.g. 1001)
    frame_end: int               # Last frame number (e.g. 1100)
    frame_count: int             # Total frames (end - start + 1)
    fps: float                   # Frames per second
    abstract_path: str           # %04d path for OTIO (image seq) or file path (video)
    width: Optional[int] = None  # Resolution — populated if versioninfo.json has it
    height: Optional[int] = None


# ---------------------------------------------------------------------------
# Discovery logic
# ---------------------------------------------------------------------------

class MediaDiscovery:
    """Scans a version folder and returns the best MediaItem found."""

    @classmethod
    def find_in_version_folder(
        cls,
        version_path: Path,
        fps: float = DEFAULT_FPS,
        fallback_frame_range: Optional[Tuple[int, int]] = None,
    ) -> Optional[MediaItem]:
        """
        Scan *version_path* for usable media.
        Priority: image sequences first (higher quality), then video files.

        *fallback_frame_range* is used for videos when duration cannot be determined
        from the file itself (requires ffprobe). If None, a 100-frame fallback is used.
        """
        if not version_path.is_dir():
            return None

        # Collect all files directly in the version folder (non-recursive)
        try:
            entries = [p for p in version_path.iterdir() if p.is_file()]
        except PermissionError:
            return None

        item = cls._detect_image_sequence(entries, fps)
        if item:
            return item

        item = cls._detect_video(entries, fps, fallback_frame_range)
        return item

    # ------------------------------------------------------------------
    # Image sequence detection
    # ------------------------------------------------------------------

    @classmethod
    def _detect_image_sequence(
        cls, files: List[Path], fps: float
    ) -> Optional[MediaItem]:
        """
        Group files that match the Prism dot-separated frame pattern.
        Returns the largest group (most frames) as the main sequence.
        """
        # Map: (base_name_without_frame, extension) -> list of (frame_int, Path)
        groups: Dict[Tuple[str, str], List[Tuple[int, Path]]] = defaultdict(list)

        for f in files:
            ext = f.suffix.lower()
            if ext not in IMAGE_SEQ_EXTENSIONS:
                continue
            m = FRAME_PATTERN.match(f.name)
            if not m:
                continue
            base, frame_str, _ext = m.group(1), m.group(2), m.group(3)
            try:
                frame_num = int(frame_str)
            except ValueError:
                continue
            groups[(base, ext)].append((frame_num, f))

        if not groups:
            return None

        # Pick the group with the most frames
        best_key = max(groups, key=lambda k: len(groups[k]))
        frames = sorted(groups[best_key], key=lambda x: x[0])
        frame_nums = [fr for fr, _ in frames]

        base_name, ext = best_key
        frame_start = frame_nums[0]
        frame_end = frame_nums[-1]
        frame_count = len(frame_nums)

        # Determine zero-padding from the actual filename
        sample_frame_str = FRAME_PATTERN.match(frames[0][1].name).group(2)
        pad = len(sample_frame_str)
        pad_fmt = f"%0{pad}d"

        abstract_path = str(frames[0][1].parent / f"{base_name}.{pad_fmt}{ext}")
        # Normalize to forward slashes for OTIO compatibility
        abstract_path = abstract_path.replace("\\", "/")

        return MediaItem(
            path=frames[0][1],
            media_type="image_sequence",
            frame_start=frame_start,
            frame_end=frame_end,
            frame_count=frame_count,
            fps=fps,
            abstract_path=abstract_path,
        )

    # ------------------------------------------------------------------
    # Video detection
    # ------------------------------------------------------------------

    @classmethod
    def _detect_video(
        cls,
        files: List[Path],
        fps: float,
        fallback_frame_range: Optional[Tuple[int, int]],
    ) -> Optional[MediaItem]:
        """
        Return the first recognised video file found.
        Duration is determined via native MP4 header parsing, then ffprobe, then fallback.
        """
        for f in sorted(files):
            if f.suffix.lower() in VIDEO_EXTENSIONS:
                duration = cls._read_mp4_duration(f, fps)
                if duration is None:
                    duration = cls._probe_video_duration(f, fps)
                if duration is not None:
                    frame_count = duration
                elif fallback_frame_range:
                    # Use the Prism shot range only to derive duration — not as a
                    # timecode. Video files always start at 0.
                    fb_in, fb_out = fallback_frame_range
                    frame_count = fb_out - fb_in + 1
                else:
                    frame_count = 100  # last resort
                frame_start = 0  # MP4/video internal time always starts at 0

                frame_end = frame_start + frame_count - 1
                abs_path = str(f).replace("\\", "/")

                return MediaItem(
                    path=f,
                    media_type="video",
                    frame_start=frame_start,
                    frame_end=frame_end,
                    frame_count=frame_count,
                    fps=fps,
                    abstract_path=abs_path,
                )
        return None

    @staticmethod
    def _read_mp4_duration(video_path: Path, fps: float) -> Optional[int]:
        """
        Parse MP4/MOV box headers to extract duration without ffprobe.
        Reads moov > mvhd box: timescale + duration_ticks → frame count.
        Returns None if parsing fails.
        """
        import struct
        try:
            size = video_path.stat().st_size
            with open(video_path, 'rb') as fh:
                chunks = [fh.read(min(65536, size))]
                if size > 65536:
                    fh.seek(max(0, size - 65536))
                    chunks.append(fh.read())
            for data in chunks:
                idx = data.find(b'mvhd')
                if idx < 4:
                    continue
                ver = data[idx + 4]
                if ver == 1:  # 64-bit timestamps
                    if idx + 36 > len(data):
                        continue
                    ts  = struct.unpack('>I', data[idx + 24:idx + 28])[0]
                    dur = struct.unpack('>Q', data[idx + 28:idx + 36])[0]
                else:  # version 0, 32-bit
                    if idx + 24 > len(data):
                        continue
                    ts  = struct.unpack('>I', data[idx + 16:idx + 20])[0]
                    dur = struct.unpack('>I', data[idx + 20:idx + 24])[0]
                if ts > 0 and dur > 0:
                    return max(1, int(round(dur / ts * fps)))
        except Exception:
            pass
        return None

    @staticmethod
    def _probe_video_duration(video_path: Path, fps: float) -> Optional[int]:
        """
        Use ffprobe to get video duration in frames.
        Returns None silently if ffprobe is not available.
        """
        import subprocess
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=nb_frames,duration",
                    "-of", "csv=p=0",
                    str(video_path),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().splitlines():
                    parts = line.split(",")
                    for part in parts:
                        part = part.strip()
                        if part.isdigit():
                            return int(part)
                        # duration in seconds
                        try:
                            secs = float(part)
                            if secs > 0:
                                return max(1, int(round(secs * fps)))
                        except ValueError:
                            pass
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
        return None
