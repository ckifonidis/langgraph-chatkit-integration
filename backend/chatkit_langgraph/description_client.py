"""
Client for communicating with the property description LangGraph API.

This module provides a client for generating AI property descriptions
using a separate LangGraph backend service.
"""

import logging
import uuid
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class DescriptionLangGraphClient:
    """
    Client for the property description generation LangGraph API.

    This client communicates with a dedicated LangGraph backend that
    generates compelling property descriptions based on property data.

    Example:
        client = DescriptionLangGraphClient(
            base_url="https://description-api.azurewebsites.net",
            assistant_id="agent"
        )
        description = await client.generate_description(
            property_data=property_dict,
            language="english"
        )
    """

    def __init__(
        self,
        base_url: str,
        assistant_id: str = "agent",
        timeout: int = 30,
    ):
        """
        Initialize the description client.

        Args:
            base_url: Base URL of the description LangGraph API
                     (e.g., "https://description-api.azurewebsites.net")
            assistant_id: LangGraph assistant/graph ID (default: "agent")
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip("/")
        self.assistant_id = assistant_id
        self.timeout = timeout
        logger.info(
            f"Initialized DescriptionLangGraphClient: "
            f"base_url={base_url}, assistant_id={assistant_id}"
        )

    def _transform_property_data(self, property_data: dict[str, Any]) -> dict[str, Any]:
        """
        Transform property data to match the description API's expected format.

        Main transformation: Convert GeoJSON geoPoint to string format.
        - From: {"type": "Point", "coordinates": [lng, lat]}
        - To: "lat,lng"
        """
        # Create a deep copy to avoid mutating the original
        import copy
        transformed = copy.deepcopy(property_data)

        # Transform geoPoint if it exists and is in GeoJSON format
        if "address" in transformed and isinstance(transformed["address"], dict):
            geo_point = transformed["address"].get("geoPoint")

            if isinstance(geo_point, dict) and "coordinates" in geo_point:
                # GeoJSON format: coordinates are [longitude, latitude]
                coords = geo_point["coordinates"]
                if isinstance(coords, list) and len(coords) == 2:
                    lng, lat = coords
                    # Convert to string format: "latitude,longitude"
                    transformed["address"]["geoPoint"] = f"{lat},{lng}"

        return transformed

    async def generate_description(
        self,
        property_data: dict[str, Any],
        language: str = "english",
        mode: str = "auto",
    ) -> str:
        """
        Generate an AI property description.

        Calls the LangGraph description API with property data and returns
        a compelling, AI-generated description.

        Args:
            property_data: Complete property object with all fields
                          (code, title, price, propertyArea, etc.)
            language: Description language (default: "english")
            mode: Generation mode (default: "auto")

        Returns:
            Generated description text

        Raises:
            httpx.TimeoutException: If request exceeds timeout
            httpx.HTTPStatusError: If API returns error status
            ValueError: If response is malformed or missing description
        """
        property_code = property_data.get("code", "unknown")
        logger.info(
            f"Generating description for property {property_code} "
            f"(language={language}, mode={mode})"
        )

        # Transform property data to match API expectations
        transformed_data = self._transform_property_data(property_data)

        # Generate unique thread ID for this request
        thread_id = str(uuid.uuid4())
        url = f"{self.base_url}/threads/{thread_id}/runs/wait"

        # Format request payload according to LangGraph API contract
        payload = {
            "assistant_id": self.assistant_id,
            "input": {
                "house_data": transformed_data,
                "description_language": language,
                "mode": mode,
            },
            "if_not_exists": "create",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()

                # Extract description from response
                # Try final_description first, fall back to final_response
                description = data.get("final_description") or data.get("final_response")

                if not description:
                    logger.error(
                        f"Response missing description fields for property {property_code}. "
                        f"Response keys: {list(data.keys())}, Full response: {data}"
                    )
                    raise ValueError(
                        "API response missing 'final_description' or 'final_response' field"
                    )

                logger.info(
                    f"Successfully generated description for property {property_code} "
                    f"({len(description)} characters)"
                )
                return description

        except httpx.TimeoutException as e:
            logger.error(
                f"Timeout generating description for property {property_code} "
                f"after {self.timeout}s: {e}"
            )
            raise

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error for property {property_code}: "
                f"status={e.response.status_code}, response: {e.response.text}"
            )
            raise

        except Exception as e:
            logger.error(
                f"Unexpected error generating description for property {property_code}: {e}",
                exc_info=True,
            )
            raise

    async def health_check(self) -> bool:
        """
        Check if the description API is reachable.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Try to hit a basic endpoint (may not exist, just checking connectivity)
                response = await client.get(f"{self.base_url}/health", follow_redirects=True)
                return response.status_code < 500
        except Exception as e:
            logger.warning(f"Description API health check failed: {e}")
            return False
