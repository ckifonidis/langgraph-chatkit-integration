"""
Property Carousel Component - Display property search results as a carousel.

This component automatically renders when LangGraph returns property query results.
"""

from __future__ import annotations

from typing import Any

from chatkit.widgets import Card
from examples.custom_widgets import create_image_carousel

from .base import CustomComponent


class PropertyCarouselComponent(CustomComponent):
    """
    Renders a property carousel when query results are present.

    Rules:
    - Activates when response_data contains "query_results"
    - query_results must be a non-empty list

    Rendering:
    - Creates horizontal scrollable carousel
    - Shows property image, title, price, and key specs
    - Enables drilldown to view full property details
    - Limits to first 20 results to avoid overwhelming UI
    """

    def __init__(self, max_items: int = 20):
        """
        Initialize the property carousel component.

        Args:
            max_items: Maximum number of properties to show in carousel (default: 20)
        """
        self.max_items = max_items

    def check_rules(self, response_data: dict[str, Any]) -> bool:
        """
        Check if this component should render.

        Args:
            response_data: LangGraph response containing query_results

        Returns:
            True if query_results exists and has items
        """
        query_results = response_data.get("query_results", [])
        return isinstance(query_results, list) and len(query_results) > 0

    def render(self, response_data: dict[str, Any]) -> Card | None:
        """
        Create a property carousel widget from query results.

        Args:
            response_data: LangGraph response with query_results field

        Returns:
            Card widget with property carousel, or None if rendering fails
        """
        try:
            properties = response_data.get("query_results", [])[:self.max_items]
            total_results = len(response_data.get("query_results", []))

            # Convert properties to carousel items
            carousel_items = []

            for prop in properties:
                # Format price
                price = prop.get("price", 0)
                price_str = f"€{price:,}" if price else "Price on request"

                # Format description with key details
                area = prop.get("propertyArea", "")
                rooms = prop.get("numberOfRooms", "")
                bathrooms = prop.get("numberOfBathrooms", "")

                desc_parts = []
                if price:
                    desc_parts.append(price_str)
                if area:
                    desc_parts.append(f"{area}sqm")
                if rooms:
                    desc_parts.append(f"{rooms} rooms")
                if bathrooms:
                    desc_parts.append(f"{bathrooms} bath")

                description = " • ".join(desc_parts)

                # Format location
                address = prop.get("address", {})
                location = address.get("prefecture", "")

                if location and description:
                    description = f"{description}\n📍 {location}"
                elif location:
                    description = f"📍 {location}"

                # Create carousel item
                carousel_items.append({
                    "id": prop.get("code", prop.get("id", "")),
                    "image_url": prop.get("defaultImagePath", ""),
                    "title": prop.get("title", "Property"),
                    "description": description,
                    "item_data": prop,  # Full property data for drilldown
                })

            # Create title with result count
            title = f"Found {total_results} Properties"
            if total_results > self.max_items:
                title = f"Found {total_results} Properties (showing first {self.max_items})"

            # Render carousel with drilldown enabled
            carousel = create_image_carousel(
                title=title,
                items=carousel_items,
                enable_drilldown=True,
                scrollable=True,
            )

            return carousel

        except Exception as e:
            # Log error but don't crash - return None to skip this component
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to render property carousel: {e}", exc_info=True)
            return None

    def get_priority(self) -> int:
        """Property carousel has medium priority."""
        return 50  # Render early but after critical components
