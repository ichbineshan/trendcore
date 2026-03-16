import json
from typing import Dict, Any

import aiohttp


class NarutoServiceError(Exception):
    """
    Raised when Naruto API returns a 5xx error (their side).

    These errors are retryable with jitter.
    """

    RETRYABLE_STATUS_CODES = {500, 502, 503, 504}

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Naruto API error {status_code}: {message}")


class NarutoAPIClient:
    """
    HTTP client for interacting with Naruto design generation API.
    """

    def __init__(self, base_url: str):
        """
        Initialize the Naruto API client.

        Args:
            base_url: Base URL for the Naruto API
        """
        self.base_url = base_url.rstrip('/')

    async def trigger_design_generation(
        self,
        design_brief: Dict[str, Any],
        webhook_url: str
    ) -> Dict[str, Any]:
        """
        Trigger design generation workflow via Naruto API.

        Args:
            design_brief: Design brief JSON to send
            webhook_url: Webhook URL for receiving results

        Returns:
            Response from Naruto API containing job_id

        Raises:
            NarutoServiceError: If the API returns 5xx error (retryable)
            aiohttp.ClientError: If the API request fails for other reasons
        """
        url = f"{self.base_url}/service/public/naruto/api/v1/generate/garments"

        design_brief_json = json.dumps(design_brief)
        design_brief_bytes = design_brief_json.encode('utf-8')

        form_data = aiohttp.FormData()
        form_data.add_field(
            'design_brief',
            design_brief_bytes,
            filename='design_brief.json',
            content_type='application/json'
        )
        form_data.add_field('webhook_url', webhook_url)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=form_data) as response:
                # Check for Naruto-side errors (5xx) - these are retryable
                if response.status in NarutoServiceError.RETRYABLE_STATUS_CODES:
                    error_text = await response.text()
                    raise NarutoServiceError(response.status, error_text)

                response.raise_for_status()
                return await response.json()

    async def poll_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Poll the status of a design generation job.

        Args:
            job_id: External job ID from Naruto API

        Returns:
            Job status and results from Naruto API

        Raises:
            NarutoServiceError: If the API returns 5xx error (retryable)
            aiohttp.ClientError: If the API request fails for other reasons
        """
        url = f"{self.base_url}/service/public/naruto/api/v1/jobs/{job_id}/garments"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # Check for Naruto-side errors (5xx) - these are retryable
                if response.status in NarutoServiceError.RETRYABLE_STATUS_CODES:
                    error_text = await response.text()
                    raise NarutoServiceError(response.status, error_text)

                response.raise_for_status()
                return await response.json()
