"""Handler for Magnific node integration with Nuke."""

import logging
from typing import Callable, Optional
from pathlib import Path

from ..upscaler import MagnificUpscaler
from ..api.models import UpscaleParams
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class MagnificNodeHandler:
    """Handles interactions between Nuke node and upscaler."""

    def __init__(self, nuke_node):
        """
        Initialize node handler.

        Args:
            nuke_node: Nuke node object
        """
        self.nuke_node = nuke_node
        self.upscaler: Optional[MagnificUpscaler] = None
        logger.info("MagnificNodeHandler initialized")

    def _get_api_key(self) -> str:
        """Get API key from node knob."""
        return self.nuke_node.knob("api_key").value()

    def _get_input_file(self) -> str:
        """Get input file path from node."""
        return self.nuke_node.knob("input_file").value()

    def _get_scale_factor(self) -> int:
        """Get scale factor from node."""
        scale_map = {0: 2, 1: 4, 2: 8, 3: 16}
        index = self.nuke_node.knob("scale_factor").value()
        return scale_map.get(int(index), 2)

    def _get_engine(self) -> str:
        """Get engine from node."""
        engine_map = {
            0: "automatic",
            1: "magnific_illusio",
            2: "magnific_sharpy",
            3: "magnific_sparkle",
        }
        index = self.nuke_node.knob("engine").value()
        return engine_map.get(int(index), "automatic")

    def _get_prompt(self) -> str:
        """Get prompt from node."""
        return self.nuke_node.knob("prompt").value()

    def _get_creativity(self) -> int:
        """Get creativity value from node."""
        return int(self.nuke_node.knob("creativity").value())

    def _get_hdr(self) -> int:
        """Get HDR value from node."""
        return int(self.nuke_node.knob("hdr").value())

    def _get_resemblance(self) -> int:
        """Get resemblance value from node."""
        return int(self.nuke_node.knob("resemblance").value())

    def _update_status(self, status: str):
        """Update status knob in Nuke."""
        try:
            self.nuke_node.knob("status").setValue(status)
            logger.debug(f"Status updated: {status}")
        except Exception as e:
            logger.warning(f"Failed to update status: {e}")

    def _update_progress(self, progress: float):
        """Update progress knob in Nuke."""
        try:
            progress_clamped = max(0, min(100, progress))
            self.nuke_node.knob("progress").setValue(progress_clamped)
            logger.debug(f"Progress updated: {progress_clamped}%")
        except Exception as e:
            logger.warning(f"Failed to update progress: {e}")

    def _update_error(self, error: str):
        """Update error message knob."""
        try:
            self.nuke_node.knob("error_message").setValue(error)
        except Exception as e:
            logger.warning(f"Failed to update error: {e}")

    def _update_output_file(self, path: str):
        """Update output file knob."""
        try:
            self.nuke_node.knob("output_file").setValue(path)
            logger.debug(f"Output file updated: {path}")
        except Exception as e:
            logger.warning(f"Failed to update output file: {e}")

    def _update_task_id(self, task_id: str):
        """Update task ID knob."""
        try:
            self.nuke_node.knob("task_id").setValue(task_id)
        except Exception as e:
            logger.warning(f"Failed to update task ID: {e}")

    def process_upscale(self) -> None:
        """
        Handle process button click - start upscaling.
        """
        logger.info("Process button clicked")

        # Validate inputs
        api_key = self._get_api_key()
        if not api_key:
            error_msg = "API key is required"
            logger.error(error_msg)
            self._update_error(error_msg)
            self._update_status("Error: Missing API key")
            return

        input_file = self._get_input_file()
        if not input_file:
            error_msg = "Input file is required"
            logger.error(error_msg)
            self._update_error(error_msg)
            self._update_status("Error: Missing input file")
            return

        input_path = Path(input_file)
        if not input_path.exists():
            error_msg = f"Input file not found: {input_file}"
            logger.error(error_msg)
            self._update_error(error_msg)
            self._update_status("Error: Input file not found")
            return

        # Create upscaler
        try:
            self.upscaler = MagnificUpscaler(api_key)
        except ValueError as e:
            error_msg = str(e)
            logger.error(error_msg)
            self._update_error(error_msg)
            self._update_status("Error: Invalid API key")
            return

        # Build parameters
        params = UpscaleParams(
            scale_factor=self._get_scale_factor(),
            engine=self._get_engine(),
            prompt=self._get_prompt(),
            creativity=self._get_creativity(),
            hdr=self._get_hdr(),
            resemblance=self._get_resemblance(),
        )

        # Validate parameters
        is_valid, error_msg = params.validate()
        if not is_valid:
            logger.error(error_msg)
            self._update_error(error_msg)
            self._update_status("Error: Invalid parameters")
            return

        # Reset UI
        self._update_progress(0)
        self._update_error("")
        self._update_status("Initializing...")
        self._update_output_file("")

        # Callbacks for upscaler
        def on_progress(elapsed: float, message: str):
            """Progress callback."""
            # Calculate percentage based on message
            if "Encoding" in message:
                progress = 5
            elif "Uploading" in message:
                progress = 10
            elif "Processing" in message:
                progress = max(20, min(80, elapsed * 2))
            elif "Downloading" in message:
                progress = 85
            elif "Saving" in message:
                progress = 95
            elif "Complete" in message:
                progress = 100
            else:
                progress = 50

            self._update_progress(progress)
            self._update_status(message)

        def on_complete(success: bool, output_path: str, error_msg: str):
            """Completion callback."""
            if success:
                self._update_progress(100)
                self._update_status("Complete!")
                self._update_output_file(output_path)
                self._update_error("")
                logger.info(f"Upscale completed successfully: {output_path}")

                # TODO: Create Read node and connect to output
                # This requires nuke context

            else:
                self._update_progress(0)
                self._update_status("Failed")
                self._update_error(error_msg)
                logger.error(f"Upscale failed: {error_msg}")

        # Start async upscaling
        success, msg = self.upscaler.upscale_image_async(
            str(input_path),
            params,
            on_complete,
            on_progress,
        )

        if success:
            self._update_status("Uploading image...")
            logger.info("Upscaling started")
        else:
            self._update_error(msg)
            self._update_status("Error: Failed to start upscale")
            logger.error(f"Failed to start upscale: {msg}")

    def cancel_upscale(self) -> None:
        """Handle cancel button click."""
        logger.info("Cancel button clicked")

        if self.upscaler and self.upscaler.is_processing():
            success, msg = self.upscaler.cancel_current_task()
            if success:
                self._update_status("Cancelling...")
                logger.info("Cancel request sent")
            else:
                logger.error(f"Failed to cancel: {msg}")
        else:
            logger.info("No upscale in progress")

    def get_status(self) -> dict:
        """Get current status information."""
        if self.upscaler:
            success, task, error = self.upscaler.get_current_task_status()
            if success:
                return {
                    "is_processing": self.upscaler.is_processing(),
                    "task_id": task.task_id if task else None,
                    "status": task.status if task else "Unknown",
                }

        return {
            "is_processing": False,
            "task_id": None,
            "status": "Idle",
        }
