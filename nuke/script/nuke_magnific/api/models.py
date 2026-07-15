"""Data models for Magnific API requests and responses."""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class TaskStatus(Enum):
    """Task status enum."""
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class UpscaleEngine(Enum):
    """Supported upscale engines."""
    AUTOMATIC = "automatic"
    MAGNIFIC_ILLUSIO = "magnific_illusio"
    MAGNIFIC_SHARPY = "magnific_sharpy"
    MAGNIFIC_SPARKLE = "magnific_sparkle"


@dataclass
class UpscaleParams:
    """Parameters for image upscaling."""

    scale_factor: int = 2  # 2, 4, 8, or 16
    engine: str = "automatic"
    prompt: str = ""
    creativity: int = 0  # -10 to 10
    hdr: int = 0  # -10 to 10
    resemblance: int = 0  # -10 to 10
    fractality: int = 0  # -10 to 10
    webhook_url: Optional[str] = None

    def validate(self) -> tuple:
        """
        Validate parameters.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.scale_factor not in [2, 4, 8, 16]:
            return False, "scale_factor must be 2, 4, 8, or 16"

        if not -10 <= self.creativity <= 10:
            return False, "creativity must be between -10 and 10"

        if not -10 <= self.hdr <= 10:
            return False, "hdr must be between -10 and 10"

        if not -10 <= self.resemblance <= 10:
            return False, "resemblance must be between -10 and 10"

        if not -10 <= self.fractality <= 10:
            return False, "fractality must be between -10 and 10"

        return True, ""

    def to_dict(self) -> dict:
        """Convert parameters to API request dictionary."""
        params = {
            "scale_factor": f"{self.scale_factor}x",
            "engine": self.engine,
        }

        if self.prompt:
            params["prompt"] = self.prompt

        if self.creativity != 0:
            params["creativity"] = self.creativity

        if self.hdr != 0:
            params["hdr"] = self.hdr

        if self.resemblance != 0:
            params["resemblance"] = self.resemblance

        if self.fractality != 0:
            params["fractality"] = self.fractality

        if self.webhook_url:
            params["webhook_url"] = self.webhook_url

        return params


@dataclass
class UpscaleTask:
    """Represents an upscale task from API response."""

    task_id: str
    status: str  # CREATED, IN_PROGRESS, COMPLETED, FAILED
    generated: List[str] = field(default_factory=list)

    def is_complete(self) -> bool:
        """Check if task is complete."""
        return self.status == "COMPLETED"

    def is_failed(self) -> bool:
        """Check if task failed."""
        return self.status == "FAILED"

    def is_processing(self) -> bool:
        """Check if task is still processing."""
        return self.status in ["CREATED", "IN_PROGRESS"]

    @classmethod
    def from_api_response(cls, data: dict) -> "UpscaleTask":
        """Create UpscaleTask from API response."""
        return cls(
            task_id=data.get("task_id", ""),
            status=data.get("status", "CREATED"),
            generated=data.get("generated", []),
        )


@dataclass
class APIError:
    """Represents an API error."""

    code: int
    message: str
    detail: Optional[str] = None

    def __str__(self) -> str:
        """String representation of error."""
        if self.detail:
            return f"API Error {self.code}: {self.message} - {self.detail}"
        return f"API Error {self.code}: {self.message}"
