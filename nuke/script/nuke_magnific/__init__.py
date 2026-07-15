"""
Nuke to Magnific integration package.

This package provides tools for upscaling images in Nuke using Magnific.ai API.
"""

__version__ = "0.1.0"
__author__ = "Mathieu"

from . import inject_external_libs
inject_external_libs.inject_external_libs()

from .upscaler import MagnificUpscaler
from .api.models import UpscaleTask, UpscaleParams

__all__ = [
    "MagnificUpscaler",
    "UpscaleTask",
    "UpscaleParams",
]
