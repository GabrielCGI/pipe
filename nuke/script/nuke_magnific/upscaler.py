"""Main upscaler orchestrator for handling complete upscale workflow."""

import threading
import logging
from typing import Callable, Optional, Tuple
from pathlib import Path

from .api.client import MagnificAPIClient
from .api.models import UpscaleTask, UpscaleParams
from .utils.image_utils import (
    encode_image_to_base64,
    save_image_png_16bit,
    get_temp_image_path,
)
from .utils.logger import setup_logger

logger = setup_logger(__name__)


class MagnificUpscaler:
    """Orchestrator for image upscaling workflow."""

    def __init__(self, api_key: str):
        """
        Initialize upscaler.

        Args:
            api_key: Freepik API key
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        self.api_key = api_key
        self.client = MagnificAPIClient(api_key)
        self._current_task_id: Optional[str] = None
        self._current_thread: Optional[threading.Thread] = None
        self._cancel_requested = False

        logger.info("MagnificUpscaler initialized")

    def upscale_image_async(
        self,
        input_path: str,
        params: UpscaleParams,
        callback_complete: Callable[[bool, str, str], None],
        callback_progress: Callable[[float, str], None] = None,
    ) -> Tuple[bool, str]:
        """
        Upscale image asynchronously (non-blocking).

        Runs upscaling in a background thread. Calls callbacks to report progress.

        Args:
            input_path: Path to input image
            params: Upscale parameters
            callback_complete: Called when complete with (success, output_path, error_msg)
            callback_progress: Called periodically with (elapsed_time, status_string)

        Returns:
            Tuple of (success, task_id or error_message)
        """
        # Check if already processing
        if self._current_thread and self._current_thread.is_alive():
            return False, "An upscale is already in progress"

        # Reset cancel flag
        self._cancel_requested = False

        # Start upscaling in background thread
        def upscale_worker():
            success, output_path, error_msg = self._upscale_image_sync(
                input_path, params, callback_progress
            )
            callback_complete(success, output_path, error_msg)

        self._current_thread = threading.Thread(target=upscale_worker, daemon=True)
        self._current_thread.start()

        logger.info(f"Started async upscale for: {input_path}")
        return True, "Upscaling started"

    def _upscale_image_sync(
        self,
        input_path: str,
        params: UpscaleParams,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> Tuple[bool, str, str]:
        """
        Upscale image synchronously (blocking).

        This is the main workflow orchestrator.

        Args:
            input_path: Path to input image
            params: Upscale parameters
            progress_callback: Optional progress callback

        Returns:
            Tuple of (success, output_path or empty, error_message)
        """
        try:
            # Step 1: Validate input
            input_file = Path(input_path)
            if not input_file.exists():
                error_msg = f"Input file not found: {input_path}"
                logger.error(error_msg)
                return False, "", error_msg

            logger.info(f"Starting upscale workflow for: {input_path}")

            # Step 2: Encode image
            if progress_callback:
                progress_callback(0, "Encoding image...")

            success, image_base64, extension = encode_image_to_base64(input_path)
            if not success:
                return False, "", image_base64  # Error message is in second return

            logger.debug(f"Image encoded successfully ({len(image_base64)} bytes)")

            # Step 3: Upload to API
            if progress_callback:
                progress_callback(10, "Uploading to Magnific API...")

            success, task_id = self.client.upload_image(image_base64, params)
            if not success:
                error_msg = f"Failed to upload image: {task_id}"
                logger.error(error_msg)
                return False, "", error_msg

            self._current_task_id = task_id
            logger.info(f"Upload successful. Task ID: {task_id}")

            # Step 4: Poll for completion
            if progress_callback:
                progress_callback(20, "Processing image on Magnific servers...")

            def poll_progress_callback(elapsed: float, status: str):
                """Wrapper for progress callback during polling."""
                # Map elapsed time to progress (0-80% during polling)
                progress = 20 + min(elapsed / 30.0 * 60, 60)  # 20-80% over 30 seconds
                if progress_callback:
                    progress_callback(progress, f"Processing... ({status})")

            success, task, error_msg = self.client.poll_until_complete(
                task_id, progress_callback=poll_progress_callback
            )

            if not success:
                logger.error(f"Polling failed: {error_msg}")
                return False, "", error_msg

            if not task.generated or len(task.generated) == 0:
                error_msg = "No output image in task result"
                logger.error(error_msg)
                return False, "", error_msg

            output_url = task.generated[0]
            logger.info(f"Upscaling complete. Output URL: {output_url}")

            # Step 5: Download result
            if progress_callback:
                progress_callback(85, "Downloading upscaled image...")

            success, image_data, error_msg = self.client.download_image(output_url)
            if not success:
                logger.error(f"Download failed: {error_msg}")
                return False, "", error_msg

            # Step 6: Save to file
            if progress_callback:
                progress_callback(95, "Saving image...")

            temp_output_path = get_temp_image_path()
            success, full_path, error_msg = save_image_png_16bit(image_data, temp_output_path)
            if not success:
                logger.error(f"Save failed: {error_msg}")
                return False, "", error_msg

            if progress_callback:
                progress_callback(100, "Complete!")

            logger.info(f"Upscaling complete. Output saved to: {full_path}")
            return True, full_path, ""

        except Exception as e:
            error_msg = f"Unexpected error in upscale workflow: {str(e)}"
            logger.exception(error_msg)
            return False, "", error_msg

    def get_current_task_status(self) -> Tuple[bool, Optional[UpscaleTask], str]:
        """
        Get status of current upscaling task.

        Returns:
            Tuple of (success, UpscaleTask or None, error_message)
        """
        if not self._current_task_id:
            return False, None, "No task in progress"

        return self.client.get_task_status(self._current_task_id)

    def cancel_current_task(self) -> Tuple[bool, str]:
        """
        Request cancellation of current upscaling task.

        Note: This only stops polling. The API task continues processing.

        Returns:
            Tuple of (success, message)
        """
        self._cancel_requested = True
        logger.info("Upscale cancellation requested")
        return True, "Cancellation requested"

    def is_processing(self) -> bool:
        """Check if upscaling is currently in progress."""
        return self._current_thread is not None and self._current_thread.is_alive()
