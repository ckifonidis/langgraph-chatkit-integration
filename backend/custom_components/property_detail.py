"""
Property Detail Component - Display full property details.

This component renders detailed property information when a user clicks
on a property in the carousel.
"""

from __future__ import annotations

from typing import Any

from chatkit.widgets import (
    Box,
    Button,
    Card,
    Caption,
    Col,
    Divider,
    Icon,
    Image,
    Row,
    Spacer,
    Text,
    Title,
    Badge,
)
from chatkit.actions import ActionConfig


def create_property_detail_card(property_data: dict[str, Any]) -> Card:
    """
    Create a detailed view card for a property.

    Displays comprehensive property information including:
    - Large image
    - Title and code
    - Price and key specs
    - Amenities
    - Location details
    - All other property attributes

    Args:
        property_data: Full property dictionary from LangGraph

    Returns:
        Card widget with detailed property information
    """
    # Extract key fields
    title = property_data.get("title", "Property Details")
    code = property_data.get("code", "")
    image_url = property_data.get("defaultImagePath", "")
    price = property_data.get("price", 0)
    price_str = f"€{price:,}" if price else "Price on request"

    # Build detail sections
    children = []

    # Header: Title + Close Button
    children.extend([
        Row(
            gap="md",
            justify="between",
            align="start",
            children=[
                Col(
                    gap="xs",
                    flex=1,
                    children=[
                        Title(value=title, size="xl", weight="bold"),
                        Caption(value=f"Code: {code}", color="secondary") if code else Spacer(minSize=0),
                    ]
                ),
                Button(
                    label="Close",
                    iconStart="close",
                    size="sm",
                    variant="ghost",
                    onClickAction=ActionConfig(
                        type="close_details",
                        handler="client"
                    ),
                ),
            ],
        ),
        Divider(spacing="md"),
    ])

    # Large Image
    if image_url:
        children.extend([
            Image(
                src=image_url,
                alt=title,
                height=400,
                fit="contain",
                radius="lg"
            ),
            Spacer(minSize="md"),
        ])

    # Price and Key Specs in a highlighted box
    area = property_data.get("propertyArea", "")
    rooms = property_data.get("numberOfRooms", "")
    bathrooms = property_data.get("numberOfBathrooms", "")
    floor = property_data.get("floor", "")

    key_specs = []
    if area:
        key_specs.append(f"{area}sqm")
    if rooms:
        key_specs.append(f"{rooms} rooms")
    if bathrooms:
        key_specs.append(f"{bathrooms} bathrooms")
    if floor is not None and floor != "":
        key_specs.append(f"Floor {floor}")

    children.append(
        Box(
            padding="md",
            background={"light": "#f0f9ff", "dark": "#1e3a5f"},
            border={"size": 1, "color": {"light": "#bae6fd", "dark": "#1e40af"}},
            radius="lg",
            children=[
                Row(
                    gap="lg",
                    justify="between",
                    align="center",
                    children=[
                        Title(value=price_str, size="2xl", weight="bold", color="primary"),
                        Text(value=" • ".join(key_specs), size="md", color="secondary"),
                    ]
                )
            ]
        )
    )

    children.append(Spacer(minSize="md"))

    # Description
    description = property_data.get("description", "")
    if description and description != "Property Description" and description.strip():
        children.extend([
            Title(value="Description", size="lg", weight="semibold"),
            Text(value=description, size="md", color="secondary"),
            Spacer(minSize="md"),
        ])

    # Amenities
    amenities = property_data.get("amenities", {})
    if amenities:
        amenity_badges = []
        amenity_map = {
            "hasPool": ("Pool", "success"),
            "hasGarden": ("Garden", "success"),
            "hasElevator": ("Elevator", "info"),
            "hasAlarm": ("Alarm", "warning"),
            "hasSafetyDoor": ("Safety Door", "info"),
            "internalStaircase": ("Internal Stairs", "secondary"),
        }

        for key, (label, color) in amenity_map.items():
            if amenities.get(key) is True:
                amenity_badges.append(
                    Badge(label=label, color=color, variant="soft", size="sm")
                )

        if amenity_badges:
            children.extend([
                Title(value="Amenities", size="lg", weight="semibold"),
                Row(gap="sm", wrap="wrap", children=amenity_badges),
                Spacer(minSize="md"),
            ])

    # Location Details
    address = property_data.get("address", {})
    if address:
        location_items = []

        prefecture = address.get("prefecture", "")
        postal_code = address.get("postalCode", "")
        country = address.get("country", "")

        if prefecture:
            location_items.append(
                Row(
                    gap="md",
                    justify="between",
                    children=[
                        Text(value="Area:", weight="medium", color="secondary"),
                        Text(value=prefecture, weight="semibold"),
                    ]
                )
            )
        if postal_code:
            location_items.append(
                Row(
                    gap="md",
                    justify="between",
                    children=[
                        Text(value="Postal Code:", weight="medium", color="secondary"),
                        Text(value=postal_code, weight="semibold"),
                    ]
                )
            )
        if country:
            location_items.append(
                Row(
                    gap="md",
                    justify="between",
                    children=[
                        Text(value="Country:", weight="medium", color="secondary"),
                        Text(value=country, weight="semibold"),
                    ]
                )
            )

        if location_items:
            children.extend([
                Title(value="Location", size="lg", weight="semibold"),
                Col(gap="xs", children=location_items),
                Spacer(minSize="md"),
            ])

    # Property Details
    detail_items = []
    detail_map = {
        "constructionYear": "Built",
        "renovationYear": "Renovated",
        "energyClass": "Energy Class",
        "heatingType": "Heating",
        "heatingControl": "Heating Control",
        "numberOfFloors": "Total Floors",
        "parkingSpace": "Parking Spaces",
        "ownershipType": "Ownership",
    }

    for key, label in detail_map.items():
        value = property_data.get(key)
        if value is not None and value != "":
            detail_items.append(
                Row(
                    gap="md",
                    justify="between",
                    padding={"y": "2xs"},
                    children=[
                        Text(value=f"{label}:", weight="medium", color="secondary", size="sm"),
                        Text(value=str(value), weight="semibold", size="sm"),
                    ]
                )
            )

    if detail_items:
        children.extend([
            Title(value="Property Details", size="lg", weight="semibold"),
            Col(gap="2xs", children=detail_items),
        ])

    # Return the complete detail card
    return Card(
        size="lg",
        padding="lg",
        background={"light": "#ffffff", "dark": "#1f2937"},
        border={"size": 2, "color": {"light": "#e5e7eb", "dark": "#374151"}},
        radius="xl",
        children=children,
    )


class PropertyCarouselComponent(CustomComponent):
    """Component that renders property search results as a carousel."""

    def __init__(self, max_items: int = 20):
        """
        Initialize the property carousel component.

        Args:
            max_items: Maximum number of properties to show (default: 20)
        """
        self.max_items = max_items

    def check_rules(self, response_data: dict[str, Any]) -> bool:
        """
        Check if property results exist.

        Returns True if:
        - response_data contains "query_results"
        - query_results is a non-empty list
        """
        query_results = response_data.get("query_results", [])
        return isinstance(query_results, list) and len(query_results) > 0

    def render(self, response_data: dict[str, Any]) -> Card | None:
        """
        Create property carousel from query results.

        Returns:
            Carousel widget showing properties with drilldown capability
        """
        try:
            properties = response_data.get("query_results", [])
            total_count = len(properties)
            display_properties = properties[:self.max_items]

            # Convert to carousel items
            items = []
            for prop in display_properties:
                # Format price
                price = prop.get("price", 0)
                price_str = f"€{price:,}" if price else "Contact for price"

                # Build description
                area = prop.get("propertyArea", "")
                rooms = prop.get("numberOfRooms", "")
                bathrooms = prop.get("numberOfBathrooms", "")

                desc_parts = [price_str]
                if area:
                    desc_parts.append(f"{area}sqm")
                if rooms:
                    desc_parts.append(f"{rooms} bed")
                if bathrooms:
                    desc_parts.append(f"{bathrooms} bath")

                # Add location
                address = prop.get("address", {})
                prefecture = address.get("prefecture", "")
                if prefecture:
                    desc_parts.append(f"📍 {prefecture}")

                items.append({
                    "id": prop.get("code", prop.get("id", "")),
                    "image_url": prop.get("defaultImagePath", ""),
                    "title": prop.get("title", "Property"),
                    "description": " • ".join(desc_parts),
                    "item_data": prop,
                })

            # Create title
            title = f"Found {total_count} Properties"
            if total_count > self.max_items:
                title += f" (showing {self.max_items})"

            # Render carousel
            return create_image_carousel(
                title=title,
                items=items,
                enable_drilldown=True,
                scrollable=True,
            )

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f"Failed to render property carousel: {e}",
                exc_info=True
            )
            return None

    def get_priority(self) -> int:
        """Medium priority - render after text but before optional components."""
        return 50
