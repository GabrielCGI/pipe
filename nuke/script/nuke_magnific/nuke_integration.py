"""
Main integration module for Nuke.

This module provides high-level functions for integrating with Nuke.
"""

import logging
from pathlib import Path

try:
    import nuke
except ImportError:
    nuke = None

logger = logging.getLogger(__name__)


def create_read_node_from_file(file_path: str, node_name: str = "Read1") -> bool:
    """
    Create a Read node in Nuke and load an image file.

    Args:
        file_path: Path to image file
        node_name: Name for the new Read node

    Returns:
        True if successful, False otherwise
    """
    if nuke is None:
        logger.error("Nuke not available")
        return False

    try:
        # Create Read node
        read_node = nuke.nodes.Read(name=node_name)
        read_node.knob("file").setValue(file_path)

        # Set other useful defaults
        read_node.knob("colorspace").setValue("linear")

        logger.info(f"Created Read node: {node_name} with file: {file_path}")
        return True

    except Exception as e:
        logger.exception(f"Error creating Read node: {e}")
        return False


def get_selected_read_node():
    """
    Get the currently selected Read node.

    Returns:
        Read node or None if not selected
    """
    if nuke is None:
        return None

    try:
        selected = nuke.selectedNodes()
        for node in selected:
            if node.Class() == "Read":
                return node
    except Exception as e:
        logger.warning(f"Error getting selected node: {e}")

    return None


def get_node_output_file() -> str:
    """
    Get the output file from the selected Read node.

    Returns:
        File path or empty string if not available
    """
    node = get_selected_read_node()
    if node:
        try:
            return node.knob("file").value()
        except Exception as e:
            logger.warning(f"Error getting node output: {e}")

    return ""


def validate_nuke_available() -> bool:
    """Check if Nuke is available."""
    return nuke is not None
