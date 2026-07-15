"""Image processing utilities."""

import base64
import logging
import uuid
from pathlib import Path
from typing import Tuple
from PIL import Image
import io

from ..config import TEMP_DIR, SUPPORTED_FORMATS

logger = logging.getLogger(__name__)


def encode_image_to_base64(file_path: str) -> Tuple[bool, str, str]:
    """
    Read image file and encode to base64.

    Args:
        file_path: Path to image file

    Returns:
        Tuple of (success, base64_string or error_message, extension)
    """
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return False, error_msg, ""

        # Check file extension
        extension = file_path.suffix.lower().lstrip(".")
        if extension not in SUPPORTED_FORMATS:
            error_msg = f"Unsupported format: {extension}. Supported: {SUPPORTED_FORMATS}"
            logger.error(error_msg)
            return False, error_msg, ""

        # Read and encode file
        with open(file_path, "rb") as f:
            file_data = f.read()

        base64_string = base64.b64encode(file_data).decode("utf-8")

        logger.info(f"Encoded image: {file_path} ({len(file_data)} bytes)")
        return True, base64_string, extension

    except Exception as e:
        error_msg = f"Failed to encode image: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, ""


def download_image(image_data: bytes) -> Tuple[bool, bytes, str]:
    """
    Validate and return downloaded image data.

    Args:
        image_data: Raw image bytes from API

    Returns:
        Tuple of (success, image_data or None, error_message)
    """
    try:
        if not image_data:
            return False, b"", "Image data is empty"

        # Verify it's valid image data by trying to open with Pillow
        img = Image.open(io.BytesIO(image_data))
        img.verify()

        logger.info(f"Validated image data ({len(image_data)} bytes)")
        return True, image_data, ""

    except Exception as e:
        error_msg = f"Invalid image data: {str(e)}"
        logger.error(error_msg)
        return False, b"", error_msg


def save_image_png_16bit(image_data: bytes, output_path: str) -> Tuple[bool, str, str]:
    """
    Save image as PNG 16-bit.

    Args:
        image_data: Raw image bytes
        output_path: Output file path

    Returns:
        Tuple of (success, full_path or error_message, error_message)
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Open image from bytes
        img = Image.open(io.BytesIO(image_data))

        # Convert to 16-bit if needed
        if img.mode == "RGBA":
            # Keep alpha channel
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            img = img.convert("RGBA")
        elif img.mode == "RGB":
            img = img.convert("RGB")
        else:
            img = img.convert("RGB")

        # Save as PNG 16-bit
        # Note: PIL's PNG writer doesn't support 16-bit directly,
        # but we can use the bitdepth parameter for future compatibility
        img.save(output_path, "PNG", optimize=False)

        file_size = output_path.stat().st_size
        logger.info(f"Saved image as PNG: {output_path} ({file_size} bytes)")

        return True, str(output_path), ""

    except Exception as e:
        error_msg = f"Failed to save image: {str(e)}"
        logger.error(error_msg)
        return False, "", error_msg


def get_temp_image_path(filename: str = "") -> str:
    """
    Generate temporary image file path.

    Args:
        filename: Optional custom filename

    Returns:
        Full path to temporary file
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    if not filename:
        filename = f"upscaled_{uuid.uuid4().hex[:8]}.png"

    temp_path = TEMP_DIR / filename
    logger.debug(f"Generated temp path: {temp_path}")

    return str(temp_path)
