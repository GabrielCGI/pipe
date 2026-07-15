"""
Nuke node callbacks for Magnific upscaler node.

This module contains callback functions that should be connected to the
Magnific node knobs in Nuke.
"""

from pathlib import Path
import threading
import time

# Try to import nuke
try:
    import nuke
except ImportError:
    nuke = None

import logging
from .node_handler import MagnificNodeHandler
from ..api.client import MagnificAPIClient
from ..api.models import UpscaleParams
from ..utils.image_utils import encode_image_to_base64, save_image_png_16bit

logger = logging.getLogger(__name__)

# Global handler instance
_node_handler = None


def setup_callbacks(nuke_node):
    """
    Setup callbacks for Magnific node.

    This should be called when the node is created.

    Args:
        nuke_node: The Magnific node instance
    """
    global _node_handler

    if nuke is None:
        logger.warning("Nuke not available - callbacks not setup")
        return

    try:
        _node_handler = MagnificNodeHandler(nuke_node)

        # Connect process button callback
        knob = nuke_node.knob("process_button")
        if knob:
            knob.setCommand(on_process_button_clicked)
            logger.info("Process button callback connected")

        # Connect cancel button callback
        knob = nuke_node.knob("cancel_button")
        if knob:
            knob.setCommand(on_cancel_button_clicked)
            logger.info("Cancel button callback connected")

        # Connect input file knob
        knob = nuke_node.knob("input_file")
        if knob:
            knob.setCommand(on_input_file_changed)
            logger.info("Input file callback connected")

        logger.info("All callbacks setup successfully")

    except Exception as e:
        logger.exception(f"Error setting up callbacks: {e}")


def on_process_button_clicked():
    """Callback when process button is clicked."""
    if nuke is None:
        return

    try:
        # Get the current node
        node = nuke.thisNode()

        if _node_handler:
            _node_handler.nuke_node = node
            _node_handler.process_upscale()
        else:
            nuke.message("Error: Node handler not initialized")

    except Exception as e:
        logger.exception(f"Error in process button callback: {e}")
        if nuke:
            nuke.message(f"Error: {str(e)}")


def on_cancel_button_clicked():
    """Callback when cancel button is clicked."""
    if nuke is None:
        return

    try:
        node = nuke.thisNode()

        if _node_handler:
            _node_handler.nuke_node = node
            _node_handler.cancel_upscale()
        else:
            nuke.message("Error: Node handler not initialized")

    except Exception as e:
        logger.exception(f"Error in cancel button callback: {e}")


def on_input_file_changed():
    """Callback when input file knob changes."""
    try:
        node = nuke.thisNode()
        input_file = node.knob("input_file").value()

        if input_file:
            # Validate file exists
            if not Path(input_file).exists():
                node.knob("error_message").setValue(
                    f"File not found: {input_file}"
                )
            else:
                node.knob("error_message").setValue("")

    except Exception as e:
        logger.warning(f"Error in input file callback: {e}")


def on_write_after_render():
    """
    Callback for Write node afterRender event.

    This function is called after the image is rendered to disk.
    It launches the Magnific upscaling process in a separate thread.
    """
    if nuke is None:
        logger.error("Nuke not available")
        return

    try:
        # Get the Write node
        write_node = nuke.thisNode()
        # Get the actual file path, evaluating expressions like [value fileName]
        rendered_file = write_node.knob("file").evaluate()

        # Get the parent Magnific group node
        parent_path = write_node.fullName().rsplit(".", 1)[0]
        magnific_node = nuke.toNode(parent_path)

        if not magnific_node:
            logger.error("Could not find parent Magnific node")
            return

        # Launch upscale in background thread
        thread = threading.Thread(
            target=_upscale_worker,
            args=(rendered_file, parent_path, magnific_node),
            daemon=True
        )
        thread.start()
        logger.info("Upscale worker thread started")

    except Exception as e:
        logger.exception(f"Error starting upscale thread: {e}")


def _update_ui(magnific_node, status=None, error=None, progress=None, task_id=None, output_file=None):
    """
    Update UI knobs from worker thread.

    This runs in the Nuke main thread to safely update the UI.
    """
    try:
        if status is not None:
            magnific_node.knob("status").setValue(status)
        if error is not None:
            magnific_node.knob("error_message").setValue(error)
        if progress is not None:
            magnific_node.knob("progress").setValue(progress)
        if task_id is not None:
            magnific_node.knob("task_id").setValue(task_id)
        if output_file is not None:
            magnific_node.knob("output_file").setValue(output_file)
    except Exception as e:
        logger.warning(f"Error updating UI: {e}")


def _upscale_worker(rendered_file: str, parent_path: str, magnific_node):
    """
    Worker function that runs in a separate thread.

    This function performs the actual upscaling work while keeping
    the Nuke UI responsive.
    """
    try:
        # Extract parameters from Magnific node
        api_key = magnific_node.knob("api_key").value()
        if not api_key:
            error_msg = "API key not set in Magnific node"
            logger.error(error_msg)
            nuke.executeInMainThread(
                lambda: _update_ui(magnific_node, status=f"Error: {error_msg}")
            )
            return

        # Scale factor - the knob returns the actual value (2x, 4x, etc)
        scale_value = magnific_node.knob("scale_factor").value()
        if isinstance(scale_value, str):
            # Remove 'x' suffix if present (e.g., "2x" -> 2)
            scale_factor = int(scale_value.rstrip("x"))
        else:
            scale_factor = int(scale_value)

        # Engine mapping - the knob returns the actual engine name
        engine = magnific_node.knob("engine").value()
        if isinstance(engine, int):
            # If it returns an index, map it
            engine_map = {
                0: "automatic",
                1: "magnific_illusio",
                2: "magnific_sharpy",
                3: "magnific_sparkle",
            }
            engine = engine_map.get(engine, "automatic")

        # Get optional parameters
        prompt = magnific_node.knob("prompt").value()
        creativity = int(magnific_node.knob("creativity").value())
        hdr = int(magnific_node.knob("hdr").value())
        resemblance = int(magnific_node.knob("resemblance").value())

        logger.info(f"Starting upscale process for: {rendered_file}")
        logger.info(f"Parameters: scale={scale_factor}x, engine={engine}")

        # Update status
        nuke.executeInMainThread(
            lambda: _update_ui(
                magnific_node,
                status="Encoding image...",
                error="",
                progress=10
            )
        )

        # Step 1: Encode image
        success, image_base64, extension = encode_image_to_base64(rendered_file)
        if not success:
            error_msg = f"Failed to encode image: {image_base64}"
            logger.error(error_msg)
            nuke.executeInMainThread(
                lambda: _update_ui(
                    magnific_node,
                    status="Error: Encoding failed",
                    error=image_base64,
                    progress=0
                )
            )
            return

        logger.debug(f"Image encoded ({len(image_base64)} bytes)")
        nuke.executeInMainThread(
            lambda: _update_ui(magnific_node, progress=20)
        )

        # Step 2: Create API client
        nuke.executeInMainThread(
            lambda: _update_ui(magnific_node, status="Creating API client...")
        )
        try:
            client = MagnificAPIClient(api_key)
        except ValueError as e:
            error_msg = str(e)
            logger.error(error_msg)
            nuke.executeInMainThread(
                lambda: _update_ui(
                    magnific_node,
                    status="Error: Invalid API key",
                    error=error_msg,
                    progress=0
                )
            )
            return

        nuke.executeInMainThread(
            lambda: _update_ui(magnific_node, progress=25)
        )

        # Step 3: Upload image
        nuke.executeInMainThread(
            lambda: _update_ui(magnific_node, status="Uploading image...")
        )
        params = UpscaleParams(
            scale_factor=scale_factor,
            engine=engine,
            prompt=prompt,
            creativity=creativity,
            hdr=hdr,
            resemblance=resemblance,
        )

        # Validate parameters
        is_valid, error_msg = params.validate()
        if not is_valid:
            logger.error(error_msg)
            nuke.executeInMainThread(
                lambda: _update_ui(
                    magnific_node,
                    status="Error: Invalid parameters",
                    error=error_msg,
                    progress=0
                )
            )
            return

        success, task_id = client.upload_image(image_base64, params)
        if not success:
            error_msg = f"Upload failed: {task_id}"
            logger.error(error_msg)
            nuke.executeInMainThread(
                lambda: _update_ui(
                    magnific_node,
                    status="Error: Upload failed",
                    error=task_id,
                    progress=0
                )
            )
            return

        nuke.executeInMainThread(
            lambda: _update_ui(
                magnific_node,
                task_id=task_id,
                progress=30
            )
        )
        logger.info(f"Image uploaded successfully. Task ID: {task_id}")

        # Step 4: Poll for completion
        nuke.executeInMainThread(
            lambda: _update_ui(magnific_node, status="Processing image...")
        )

        def progress_callback(elapsed, status):
            """Update status during polling."""
            # Calculate progress percentage
            progress = min(80, 30 + (elapsed / 10))  # Scale from 30% to 80%
            nuke.executeInMainThread(
                lambda: _update_ui(
                    magnific_node,
                    progress=progress,
                    status=f"{status} ({elapsed:.0f}s)"
                )
            )

        success, task, error = client.poll_until_complete(
            task_id, progress_callback=progress_callback
        )
        if not success:
            error_msg = f"Processing failed: {error}"
            logger.error(error_msg)
            nuke.executeInMainThread(
                lambda: _update_ui(
                    magnific_node,
                    status="Error: Processing failed",
                    error=error,
                    progress=0
                )
            )
            return

        if not task.generated:
            error_msg = "No output image in task result"
            logger.error(error_msg)
            nuke.executeInMainThread(
                lambda: _update_ui(
                    magnific_node,
                    status="Error: No output image",
                    error=error_msg,
                    progress=0
                )
            )
            return

        nuke.executeInMainThread(
            lambda: _update_ui(magnific_node, progress=80)
        )
        logger.info(f"Task completed. Output URL: {task.generated[0]}")

        # Step 5: Download image
        nuke.executeInMainThread(
            lambda: _update_ui(magnific_node, status="Downloading image...")
        )
        success, image_data, error = client.download_image(task.generated[0])
        if not success:
            error_msg = f"Download failed: {error}"
            logger.error(error_msg)
            nuke.executeInMainThread(
                lambda: _update_ui(
                    magnific_node,
                    status="Error: Download failed",
                    error=error,
                    progress=0
                )
            )
            return

        nuke.executeInMainThread(
            lambda: _update_ui(magnific_node, progress=90)
        )
        logger.info(f"Image downloaded ({len(image_data)} bytes)")

        # Step 6: Save image
        nuke.executeInMainThread(
            lambda: _update_ui(magnific_node, status="Saving result...")
        )
        output_path = Path(rendered_file).parent / f"upscaled_{Path(rendered_file).stem}.png"
        success, full_path, error = save_image_png_16bit(image_data, str(output_path))
        # Convert backslashes to forward slashes for Nuke compatibility
        full_path = full_path.replace("\\", "/")
        if not success:
            error_msg = f"Save failed: {error}"
            logger.error(error_msg)
            nuke.executeInMainThread(
                lambda: _update_ui(
                    magnific_node,
                    status="Error: Save failed",
                    error=error,
                    progress=0
                )
            )
            return

        nuke.executeInMainThread(
            lambda: _update_ui(magnific_node, progress=95)
        )
        logger.info(f"Image saved: {full_path}")

        # Step 7: Update Read node (ReadMagnific) and switch to it
        try:
            read_node = nuke.toNode(f"{parent_path}.ReadMagnific")
            magnific_switch = nuke.toNode(f"{parent_path}.magniSwitch")

            if read_node and magnific_switch:
                def update_reload_and_switch():
                    # Update and reload the Read node
                    read_node.knob("file").setValue(full_path)
                    read_node.knob("reload").execute()
                    # Switch to the Magnific result (input 1)
                    magnific_switch.knob("which").setValue(1)

                nuke.executeInMainThread(update_reload_and_switch)
                logger.info(f"Updated ReadMagnific node with: {full_path}, reloaded, and switched magniSwitch to input 1")
            else:
                if not read_node:
                    logger.warning("ReadMagnific node not found")
                if not magnific_switch:
                    logger.warning("magniSwitch node not found")
        except Exception as e:
            logger.warning(f"Could not update ReadMagnific node or switch: {e}")

        # Step 8: Update output file knob and show success
        nuke.executeInMainThread(
            lambda: _update_ui(
                magnific_node,
                status="Complete!",
                error="",
                progress=100,
                output_file=full_path
            )
        )
        logger.info("Upscale process completed successfully")

    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Error in upscale worker: {e}")
        nuke.executeInMainThread(
            lambda: _update_ui(
                magnific_node,
                status="Error",
                error=error_msg,
                progress=0
            )
        )
