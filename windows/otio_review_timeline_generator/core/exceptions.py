"""
core/exceptions.py — Custom exceptions for the OTIO Review Generator.
"""


class OtioReviewError(Exception):
    """Base exception for all tool errors."""


class InvalidProjectError(OtioReviewError):
    """Raised when a path does not point to a valid Prism project."""


class NoMediaFoundError(OtioReviewError):
    """Raised when no usable media is found for a shot/task/version combination."""


class PipelineConfigError(OtioReviewError):
    """Raised when pipeline.json cannot be read or parsed."""


class ShotInfoError(OtioReviewError):
    """Raised when shotInfo.json cannot be read or parsed."""


class TimelineBuildError(OtioReviewError):
    """Raised when the OTIO timeline cannot be assembled or exported."""
