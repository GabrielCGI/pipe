"""
Configuration and constants for Magnific API integration.
"""

from pathlib import Path

# API Endpoints
MAGNIFIC_API_BASE_URL = "https://api.freepik.com/v1"
MAGNIFIC_UPSCALER_ENDPOINT = f"{MAGNIFIC_API_BASE_URL}/ai/image-upscaler"
MAGNIFIC_UPSCALER_CREATIVE_ENDPOINT = f"{MAGNIFIC_API_BASE_URL}/ai/image-upscaler"  # Same endpoint, use 'engine' param for creative
MAGNIFIC_UPSCALER_PRECISION_V2_ENDPOINT = f"{MAGNIFIC_API_BASE_URL}/ai/image-upscaler"  # Same endpoint, use 'engine' param

# Headers
DEFAULT_HEADERS = {
    "User-Agent": "nuke-magnific/0.1.0",
    "Content-Type": "application/json",
}

# Timeout settings (seconds)
REQUEST_TIMEOUT = 30
POLL_TIMEOUT = 300
POLL_INTERVAL = 5

# File paths
LOG_DIR = Path.home() / ".nuke"
LOG_FILE = LOG_DIR / "magnific_upscaler.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Supported scales
SUPPORTED_SCALES = [2, 4, 8, 16]

# Supported engines
SUPPORTED_ENGINES = {
    "automatic": "Automatic (best for most images)",
    "magnific_illusio": "Illusio (illustrations, landscapes, removes artifacts)",
    "magnific_sharpy": "Sharpy (realistic photos, sharpest details)",
    "magnific_sparkle": "Sparkle (balanced, removes artifacts)",
}

# Image formats
SUPPORTED_FORMATS = ["png", "jpg", "jpeg"]
DEFAULT_OUTPUT_FORMAT = "png"

# Temporary directory for downloads
TEMP_DIR = Path.home() / ".nuke" / "magnific_temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
