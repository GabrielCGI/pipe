"""HTTP client for Magnific API communication."""

import requests
import time
import logging
from typing import Optional, Tuple
from .models import UpscaleTask, UpscaleParams
from ..config import (
    MAGNIFIC_UPSCALER_CREATIVE_ENDPOINT,
    REQUEST_TIMEOUT,
    POLL_TIMEOUT,
    POLL_INTERVAL,
    DEFAULT_HEADERS,
)

logger = logging.getLogger(__name__)


class MagnificAPIClient:
    """Client for communicating with Magnific API."""

    def __init__(self, api_key: str):
        """
        Initialize API client.

        Args:
            api_key: Freepik API key for authentication
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("API key must be a non-empty string")

        self.api_key = api_key
        self.base_url = MAGNIFIC_UPSCALER_CREATIVE_ENDPOINT

    def _get_headers(self) -> dict:
        """Get request headers with authentication."""
        headers = DEFAULT_HEADERS.copy()
        headers["x-freepik-api-key"] = self.api_key
        return headers

    def upload_image(self, image_base64: str, params: UpscaleParams) -> Tuple[bool, str]:
        """
        Upload image for upscaling.

        Args:
            image_base64: Base64-encoded image data
            params: Upscale parameters

        Returns:
            Tuple of (success, task_id or error_message)
        """
        if not image_base64:
            return False, "Image data cannot be empty"

        # Validate parameters
        is_valid, error_msg = params.validate()
        if not is_valid:
            return False, error_msg

        try:
            payload = {"image": image_base64}
            payload.update(params.to_dict())

            logger.info(f"Uploading image to Magnific API (scale: {params.scale_factor}x)")
            logger.debug(f"Request URL: {self.base_url}")

            response = requests.post(
                self.base_url,
                json=payload,
                headers=self._get_headers(),
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            data = response.json()
            task_data = data.get("data", {})
            task_id = task_data.get("task_id")

            if not task_id:
                error_msg = "No task_id in API response"
                logger.error(error_msg)
                return False, error_msg

            logger.info(f"Successfully uploaded image. Task ID: {task_id}")
            return True, task_id

        except requests.exceptions.Timeout:
            error_msg = f"API request timeout (>{REQUEST_TIMEOUT}s)"
            logger.error(error_msg)
            return False, error_msg

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            logger.error(f"HTTP Error {status_code}: {e.response.text}")

            if status_code == 401:
                return False, "Invalid API key"
            elif status_code == 400:
                return False, f"Invalid request: {e.response.text}"
            elif status_code == 429:
                return False, "Rate limit exceeded"
            else:
                return False, f"API Error {status_code}: {e.response.reason}"

        except Exception as e:
            error_msg = f"Unexpected error during upload: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_task_status(self, task_id: str) -> Tuple[bool, Optional[UpscaleTask], str]:
        """
        Get status of upscale task.

        Args:
            task_id: Task ID to check

        Returns:
            Tuple of (success, UpscaleTask or None, error_message)
        """
        if not task_id:
            return False, None, "Task ID cannot be empty"

        try:
            logger.debug(f"Checking status for task: {task_id}")

            # Use specific task endpoint to get individual task status
            task_url = f"{self.base_url}/{task_id}"
            response = requests.get(
                task_url,
                headers=self._get_headers(),
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            data = response.json()
            task_data = data.get("data", {})

            if not task_data:
                error_msg = f"Task {task_id} not found"
                logger.warning(error_msg)
                return False, None, error_msg

            task = UpscaleTask.from_api_response(task_data)
            logger.debug(f"Task {task_id} status: {task.status}")
            return True, task, ""

        except requests.exceptions.Timeout:
            error_msg = f"API request timeout (>{REQUEST_TIMEOUT}s)"
            logger.error(error_msg)
            return False, None, error_msg

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            logger.error(f"HTTP Error {status_code}: {e.response.text}")

            if status_code == 401:
                return False, None, "Invalid API key"
            else:
                return False, None, f"API Error {status_code}: {e.response.reason}"

        except Exception as e:
            error_msg = f"Unexpected error checking status: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def poll_until_complete(
        self,
        task_id: str,
        timeout: int = POLL_TIMEOUT,
        check_interval: int = POLL_INTERVAL,
        progress_callback=None,
    ) -> Tuple[bool, Optional[UpscaleTask], str]:
        """
        Poll API until task is complete or timeout.

        Args:
            task_id: Task ID to poll
            timeout: Maximum time to wait in seconds
            check_interval: Time between checks in seconds
            progress_callback: Optional callback for progress updates
                              Called with (elapsed_time, task_status_string)

        Returns:
            Tuple of (success, UpscaleTask or None, error_message)
        """
        logger.info(f"Polling task {task_id} (timeout: {timeout}s, interval: {check_interval}s)")

        start_time = time.time()

        while True:
            elapsed = time.time() - start_time

            # Check timeout
            if elapsed > timeout:
                error_msg = f"Polling timeout after {timeout}s"
                logger.error(error_msg)
                return False, None, error_msg

            # Get task status
            success, task, error = self.get_task_status(task_id)

            if not success:
                logger.warning(f"Failed to get task status: {error}")
                time.sleep(check_interval)
                continue

            if progress_callback:
                progress_callback(elapsed, task.status)

            # Check if task is complete
            if task.is_complete():
                logger.info(f"Task {task_id} completed successfully")
                return True, task, ""

            if task.is_failed():
                error_msg = f"Task {task_id} failed"
                logger.error(error_msg)
                return False, task, error_msg

            # Still processing, wait and retry
            logger.debug(f"Task {task_id} still processing... ({elapsed:.1f}s elapsed)")
            time.sleep(check_interval)

    def download_image(self, url: str) -> Tuple[bool, Optional[bytes], str]:
        """
        Download image from URL.

        Args:
            url: Image URL to download

        Returns:
            Tuple of (success, image_data or None, error_message)
        """
        if not url:
            return False, None, "URL cannot be empty"

        try:
            logger.info(f"Downloading image from: {url}")

            response = requests.get(url, timeout=REQUEST_TIMEOUT, stream=True)
            response.raise_for_status()

            # Get file size
            content_length = response.headers.get("content-length")
            if content_length:
                logger.debug(f"Downloading {int(content_length) / 1024 / 1024:.2f}MB")

            image_data = response.content

            logger.info(f"Successfully downloaded image ({len(image_data)} bytes)")
            return True, image_data, ""

        except requests.exceptions.Timeout:
            error_msg = f"Download timeout (>{REQUEST_TIMEOUT}s)"
            logger.error(error_msg)
            return False, None, error_msg

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error {e.response.status_code}: {e.response.reason}"
            logger.error(error_msg)
            return False, None, error_msg

        except Exception as e:
            error_msg = f"Unexpected error downloading image: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
