"""
Property Carousel Component - Display property search results as a carousel.

This component automatically renders when LangGraph returns property query results.
"""

from __future__ import annotations

from typing import Any

from chatkit.widgets import ListView

from .base import CustomComponent
from .widgets import create_property_listview


class PropertyCarouselComponent(CustomComponent):
    """
    Renders a property ListView when query results are present.

    Rules:
    - Activates when response_data contains "query_results"
    - query_results must be a non-empty list

    Rendering:
    - Creates a ChatKit ListView with property items
    - Shows property image, title, price Badge, specs, and location with icon
    - Enables drilldown to view full property details
    - Built-in "show more" functionality after limit (default: 20)
    - Follows ChatKit widget best practices for clean, semantic UI
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

    def render(self, response_data: dict[str, Any], user_preferences: dict[str, Any] | None = None) -> ListView | None:
        """
        Create a property ListView widget from query results.

        Args:
            response_data: LangGraph response with query_results field
            user_preferences: Optional user preferences with 'favorites' and 'hidden' lists

        Returns:
            ListView widget with property items, or None if rendering fails
        """
        try:
            properties = response_data.get("query_results", [])

            # Filter out hidden properties
            if user_preferences:
                hidden = set(user_preferences.get('hidden', {}).keys())
                if hidden:
                    properties = [
                        prop for prop in properties
                        if prop.get('code') not in hidden
                    ]
                    print(f"[DEBUG] Filtered {len(response_data.get('query_results', [])) - len(properties)} hidden properties")

            # If all properties are hidden, return None
            if not properties:
                print("[DEBUG] All properties were hidden, returning None")
                return None

            # Limit to max_items after filtering
            properties = properties[:self.max_items]

            # Convert properties to ListView items
            listview_items = []

            for prop in properties:
                # Format price prominently
                price = prop.get("price", 0)
                price_str = f"€{price:,}" if price else "Price on request"

                # Format property specs
                area = prop.get("propertyArea", "")
                rooms = prop.get("numberOfRooms", "")
                bathrooms = prop.get("numberOfBathrooms", "")
                floor = prop.get("floor", "")

                spec_parts = []
                if area:
                    spec_parts.append(f"{area}sqm")
                if rooms:
                    spec_parts.append(f"{rooms} rooms")
                if bathrooms:
                    spec_parts.append(f"{bathrooms} bath")
                if floor is not None and floor != "":
                    # Format floor: "1" -> "Floor 1", non-numeric stays as-is
                    floor_str = f"Floor {floor}" if str(floor).isdigit() else str(floor)
                    spec_parts.append(floor_str)

                specs_line = " • ".join(spec_parts)

                # Extract description for preview
                description = prop.get("description", "")

                # Format location
                address = prop.get("address", {})
                location = address.get("prefecture", "")

                # Create ListView item with clean data structure
                listview_items.append({
                    "id": prop.get("code", prop.get("id", "")),
                    "image_url": prop.get("defaultImagePath", ""),
                    "title": prop.get("title", "Property"),
                    "price": price_str,      # Badge display
                    "specs": specs_line,     # Caption text
                    "description": description,  # Description preview
                    "location": location,    # Location with icon
                    "item_data": prop,       # Full property data for drilldown
                })

            # Extract favorites set
            favorites = set(user_preferences.get('favorites', {}).keys()) if user_preferences else set()

            # Render ListView with built-in "show more"
            listview = create_property_listview(
                items=listview_items,
                limit=self.max_items,
                favorites=favorites,
            )

            return listview

        except Exception as e:
            # Log error but don't crash - return None to skip this component
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to render property ListView: {e}", exc_info=True)
            return None

    def get_priority(self) -> int:
        """Property carousel has medium priority."""
        return 50  # Render early but after critical components
