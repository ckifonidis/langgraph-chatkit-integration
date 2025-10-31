"""
Property Widget Components.

Reusable widget functions for property search UI.
"""

from typing import Any, Dict, List

from chatkit.actions import ActionConfig
from chatkit.widgets import (
    Badge,
    Button,
    Caption,
    Col,
    Icon,
    Image,
    ListView,
    ListViewItem,
    Row,
    Text,
)


def create_property_listview(
    items: List[Dict[str, Any]],
    limit: int = 20,
    favorites: List[str] = None,
) -> ListView:
    """
    Create a professional property ListView following ChatKit best practices.

    Each property item should have:
    - id: Unique identifier
    - image_url: Property image URL
    - title: Property title/description
    - price: Formatted price string (e.g., "€115,000")
    - specs: Property specifications (e.g., "224sqm • 4 rooms • 1 bath")
    - location: Location name
    - item_data: Full property data for drilldown

    Args:
        items: List of property items
        limit: Max items before "show more" (default: 20)
        favorites: List of favorited property codes (default: [])

    Returns:
        ListView widget with property cards

    Example:
        >>> listview = create_property_listview(
        ...     items=[{
        ...         "id": "prop_1",
        ...         "image_url": "https://example.com/property.jpg",
        ...         "title": "Maisonette 224sqm, Nea Fokea",
        ...         "price": "€115,000",
        ...         "specs": "224sqm • 4 rooms • 1 bath",
        ...         "location": "Nea Fokea",
        ...         "item_data": {...}
        ...     }],
        ...     limit=20,
        ...     favorites=["prop_1"]
        ... )
    """
    if favorites is None:
        favorites = []

    list_items = []

    for item in items:
        item_id = item.get("id", "")
        is_favorited = item_id in favorites

        # Build property card content
        property_content = [
            Image(
                src=item.get("image_url", ""),
                alt=item.get("title", "Property"),
                height=120,
                fit="cover",
                radius="lg",
            ),
            Col(
                gap=1,
                flex=1,
                children=[
                    child for child in [
                        # Title
                        Text(
                            value=item.get("title", "Property"),
                            weight="semibold",
                            size="sm",
                            maxLines=2,
                        ),
                        # Price Badge - prominent display
                        Badge(
                            label=item.get("price", "Price on request"),
                            color="success",
                            size="md",
                            variant="soft",
                        ),
                        # Specifications
                        Caption(
                            value=item.get("specs", ""),
                            size="sm",
                            color="secondary",
                        ) if item.get("specs") else None,
                        # Description preview (first 2 lines with truncation)
                        Caption(
                            value=item.get("description", ""),
                            size="sm",
                            color="secondary",
                            maxLines=2,
                            truncate=True,
                        ) if item.get("description") else None,
                        # Location with icon
                        Row(
                            gap=1,
                            align="center",
                            children=[
                                Icon(name="map-pin", size="sm", color="secondary"),
                                Caption(
                                    value=item.get("location", ""),
                                    size="sm",
                                    color="secondary",
                                ),
                            ],
                        ) if item.get("location") else None,
                    ] if child is not None
                ],
            ),
            # Action buttons (favorite + hide)
            Col(
                gap=1,
                align="start",
                children=[
                    create_favorite_button(item_id, is_favorited=(item_id in favorites)),
                    create_hide_button(item_id),
                ],
            ),
        ]

        # Filter out None values
        property_content = [child for child in property_content if child is not None]

        # Create ListViewItem with click action (client-side handler for modal)
        list_item = ListViewItem(
            key=item_id,
            gap=3,
            align="stretch",
            onClickAction=ActionConfig(
                type="view_item_details",
                handler="client",  # Handle on frontend to show modal
                payload={
                    "item_id": item_id,
                    "item_data": item.get("item_data", item),
                },
            ),
            children=property_content,
        )

        list_items.append(list_item)

    return ListView(
        children=list_items,
        limit=limit,  # Built-in "show more" functionality
    )


def create_favorite_button(
    property_code: str,
    is_favorited: bool = False
) -> Button:
    """
    Create a favorite button for property cards.

    Args:
        property_code: Property code (e.g., "PROP001")
        is_favorited: Whether property is currently favorited

    Returns:
        Button widget configured for server-side handling

    Example:
        >>> button = create_favorite_button("PROP123", is_favorited=True)
    """
    return Button(
        label="",  # Icon only
        iconStart="star-filled" if is_favorited else "star",
        size="xs",
        variant="ghost",
        color="warning" if is_favorited else "secondary",
        onClickAction=ActionConfig(
            type="toggle_favorite",
            # Server-side handling: backend will update preferences and re-render widget
            payload={"propertyCode": property_code}
        )
    )


def create_hide_button(property_code: str) -> Button:
    """
    Create a hide button for property cards.

    Args:
        property_code: Property code

    Returns:
        Button widget configured for server-side handling

    Example:
        >>> button = create_hide_button("PROP123")
    """
    return Button(
        label="",  # Icon only
        iconStart="empty-circle",  # Using empty-circle as a substitute for eye-slash
        size="xs",
        variant="ghost",
        color="secondary",
        onClickAction=ActionConfig(
            type="hide_property",
            # Server-side handling: backend will update preferences and re-render widget
            payload={"propertyCode": property_code}
        )
    )
