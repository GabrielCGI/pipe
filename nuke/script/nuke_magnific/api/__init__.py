"""API client and models for Magnific integration."""

from .client import MagnificAPIClient
from .models import UpscaleTask, UpscaleParams

__all__ = [
    "MagnificAPIClient",
    "UpscaleTask",
    "UpscaleParams",
]
