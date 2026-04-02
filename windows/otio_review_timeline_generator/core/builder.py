"""
core/builder.py — OTIO timeline builder.

Assembles an otio.schema.Timeline from a list of (ShotEntry, task, MediaItem)
tuples and exports it to disk.

One video Track is created per task. Shots missing media receive an
otio.schema.Gap so timeline sync is preserved.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

try:
    import opentimelineio as otio
    from opentimelineio.opentime import RationalTime, TimeRange
except ImportError as exc:
    raise ImportError(
        "opentimelineio is not installed. Run: pip install opentimelineio"
    ) from exc

from core.media import MediaItem
from core.scanner import ShotEntry
from core.exceptions import TimelineBuildError


# ---------------------------------------------------------------------------
# Input type
# ---------------------------------------------------------------------------

class ShotMedia(NamedTuple):
    """Bundles a shot, the task name, and the resolved media (may be None)."""
    shot: ShotEntry
    task: str
    media: Optional[MediaItem]  # None -> Gap will be inserted
    version_str: str            # e.g. "v003" (for metadata / display)


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

class TimelineBuilder:
    """
    Builds an OTIO Timeline from a collection of ShotMedia entries.

    Each unique task gets its own video Track. Shots are ordered as provided.
    Shots without media are represented as Gaps.
    """

    def __init__(self, fps: float = 25.0, use_file_uri: bool = False) -> None:
        self.fps = fps
        self.use_file_uri = use_file_uri  # True for Hiero, False for RV

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        shot_media_list: List[ShotMedia],
        timeline_name: str = "Review",
    ) -> otio.schema.Timeline:
        """
        Construct and return an OTIO Timeline.

        *shot_media_list* is a flat list; if multiple tasks are included, entries
        for the same shot but different tasks are expected to appear together or
        can be interleaved — they are grouped by task internally.
        """
        if not shot_media_list:
            raise TimelineBuildError("No shot media provided; cannot build timeline.")

        # Group by task to produce one track per task
        tasks_ordered: List[str] = []
        by_task: Dict[str, List[ShotMedia]] = {}
        for sm in shot_media_list:
            if sm.task not in by_task:
                tasks_ordered.append(sm.task)
                by_task[sm.task] = []
            by_task[sm.task].append(sm)

        timeline = otio.schema.Timeline(name=timeline_name)

        for task in tasks_ordered:
            track = self._build_track(task, by_task[task])
            timeline.tracks.append(track)

        return timeline

    @staticmethod
    def export(timeline: otio.schema.Timeline, output_path: Path) -> None:
        """Write the timeline to *output_path* using the appropriate OTIO adapter."""
        try:
            otio.adapters.write_to_file(timeline, str(output_path))
        except Exception as exc:
            raise TimelineBuildError(f"Failed to export timeline: {exc}") from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_track(self, task: str, entries: List[ShotMedia]) -> otio.schema.Track:
        track = otio.schema.Track(
            name=task,
            kind=otio.schema.TrackKind.Video,
        )
        for sm in entries:
            item = self._make_clip(sm) if sm.media else self._make_gap(sm)
            track.append(item)
        return track

    def _make_clip(self, sm: ShotMedia) -> otio.schema.Clip:
        """Create a Clip for a shot with resolved media."""
        media = sm.media
        shot = sm.shot

        # Prefer the frame range from shotInfo over what's on disk
        # (disk may be partial / still rendering)
        shot_frame_in, shot_frame_out = shot.frame_range
        shot_frame_count = shot_frame_out - shot_frame_in + 1

        # available_range describes what the media file actually contains
        available_range = TimeRange(
            start_time=RationalTime(media.frame_start, self.fps),
            duration=RationalTime(media.frame_count, self.fps),
        )

        # source_range is what portion of the media we want to use in the timeline.
        # Videos always start at 0 internally — using shot_frame_in (e.g. 1001) as
        # start_time would make RV seek a non-existent frame and display a still image.
        # Image sequences are physically numbered from shot_frame_in, so we can use it.
        if media.media_type == "video":
            source_start = RationalTime(media.frame_start, self.fps)
            source_duration = RationalTime(media.frame_count, self.fps)
        elif (media.frame_start <= shot_frame_in
                and shot_frame_out <= media.frame_end):
            source_start = RationalTime(shot_frame_in, self.fps)
            source_duration = RationalTime(shot_frame_count, self.fps)
        else:
            # Image seq doesn't fully cover the shot range — use what we have
            source_start = RationalTime(media.frame_start, self.fps)
            source_duration = RationalTime(media.frame_count, self.fps)

        source_range = TimeRange(
            start_time=source_start,
            duration=source_duration,
        )

        ref = self._make_media_reference(media, available_range)

        clip = otio.schema.Clip(
            name=shot.display_name,
            media_reference=ref,
            source_range=source_range,
        )

        # Attach Prism metadata for round-tripping / downstream tools
        clip.metadata["prism"] = {
            "sequence": shot.sequence,
            "shot": shot.shot,
            "task": sm.task,
            "version": sm.version_str,
            "frame_in": shot_frame_in,
            "frame_out": shot_frame_out,
            "media_type": media.media_type,
        }

        return clip

    # Pattern to parse abstract_path: /path/prefix.%04d.ext
    _ABSTRACT_RE = re.compile(r"^(.*[/\\])(.+\.)%0(\d+)d(\.\w+)$")

    @staticmethod
    def _to_file_uri(path: str) -> str:
        """Convert a Windows or UNC path to a file:// URI (for Hiero compatibility)."""
        path = path.replace("\\", "/")
        if len(path) >= 2 and path[1] == ":":
            return "file:///" + path
        if path.startswith("//"):
            return "file:" + path
        return path

    def _make_media_reference(
        self, media: MediaItem, available_range
    ):
        """
        Return the appropriate OTIO media reference.

        Image sequences  → ImageSequenceReference (RV reads these natively)
        Video files      → ExternalReference

        use_file_uri=True  → file:/// URIs for Hiero Player
        use_file_uri=False → raw paths for OpenRV
        """
        if media.media_type == "image_sequence":
            m = self._ABSTRACT_RE.match(media.abstract_path)
            if m:
                raw_base = m.group(1).replace("\\", "/")
                url_base = self._to_file_uri(raw_base) if self.use_file_uri else raw_base
                name_prefix = m.group(2)
                pad = int(m.group(3))
                name_suffix = m.group(4)
                return otio.schema.ImageSequenceReference(
                    target_url_base=url_base,
                    name_prefix=name_prefix,
                    name_suffix=name_suffix,
                    start_frame=media.frame_start,
                    frame_step=1,
                    frame_zero_padding=pad,
                    rate=self.fps,
                    available_range=available_range,
                )
            # Fallback: abstract_path doesn't match expected pattern
        target = self._to_file_uri(media.abstract_path) if self.use_file_uri else media.abstract_path
        return otio.schema.ExternalReference(
            target_url=target,
            available_range=available_range,
        )

    def _make_gap(self, sm: ShotMedia) -> otio.schema.Gap:
        """Insert a Gap for a shot with no media, preserving timeline sync."""
        shot = sm.shot
        frame_in, frame_out = shot.frame_range
        frame_count = frame_out - frame_in + 1

        gap = otio.schema.Gap(
            source_range=TimeRange(
                start_time=RationalTime(0, self.fps),
                duration=RationalTime(frame_count, self.fps),
            ),
            name=f"{shot.display_name} [MISSING]",
        )
        gap.metadata["prism"] = {
            "sequence": shot.sequence,
            "shot": shot.shot,
            "task": sm.task,
            "version": sm.version_str,
            "missing": True,
        }
        return gap
