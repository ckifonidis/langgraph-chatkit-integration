"""
Custom Widget Library for LangGraph ChatKit Integration.

This module provides reusable widget compositions for common UI patterns.
"""

from typing import List, Dict, Any
from chatkit.widgets import (
    Card,
    Row,
    Col,
    Image,
    Text,
    Button,
    Caption,
    Box,
    Title,
    Divider,
    Spacer,
    Badge,
    ListView,
    ListViewItem,
    Icon,
)
from chatkit.actions import ActionConfig


def create_image_carousel(
    items: List[Dict[str, Any]],
    title: str = None,
    scrollable: bool = True,
    enable_drilldown: bool = False,
) -> Card:
    """
    Create a horizontal carousel of images with optional drilldown.

    Each item should have:
    - image_url: URL of the image to display
    - title: Title text below the image
    - description: Optional short description text
    - link_url: Optional URL to open when clicked (if drilldown disabled)
    - id: Unique identifier for the item (required for drilldown)
    - item_data: Full data dict to pass when drilldown is clicked

    Args:
        items: List of carousel items with image, title, link
        title: Optional title for the carousel
        scrollable: Enable horizontal scrolling (default: True)
        enable_drilldown: Make items clickable to show details (default: False)

    Returns:
        Card widget with horizontal scrollable carousel

    Example:
        >>> # Simple carousel with links
        >>> carousel = create_image_carousel(
        ...     title="Featured Products",
        ...     items=[{
        ...         "id": "prod_1",
        ...         "image_url": "https://example.com/product1.jpg",
        ...         "title": "Product 1",
        ...         "description": "Amazing product",
        ...         "link_url": "https://example.com/product1"
        ...     }]
        ... )
        >>>
        >>> # Drilldown carousel
        >>> carousel = create_image_carousel(
        ...     title="Products",
        ...     items=[{
        ...         "id": "prod_1",
        ...         "image_url": "...",
        ...         "title": "Product 1",
        ...         "description": "Short desc",
        ...         "item_data": {"price": "$99", "stock": 15, "full_desc": "..."}
        ...     }],
        ...     enable_drilldown=True
        ... )
    """
    carousel_items = []

    for item in items:
        item_id = item.get("id", item["title"])

        # Build item content with professional spacing
        item_content = [
            # Image - optimized size for better text visibility
            Image(
                src=item["image_url"],
                alt=item.get("title", "Image"),
                height=150,
                fit="cover",
                radius="lg",
                flush=True,
            ),
            # Title - property name
            Text(
                value=item["title"],
                size="md",
                weight="bold",
                truncate=True,
                maxLines=2,
                padding={"top": "md", "bottom": "xs"},
            ),
        ]

        # Add price prominently if available
        if item.get("price"):
            item_content.append(
                Text(
                    value=item["price"],
                    size="xl",
                    weight="bold",
                    color="primary",
                    padding={"bottom": "xs"},
                )
            )

        # Add specs if available
        if item.get("specs"):
            item_content.append(
                Caption(
                    value=item["specs"],
                    size="sm",
                    color="secondary",
                    padding={"bottom": "xs"},
                )
            )

        # Add location if available
        if item.get("location"):
            item_content.append(
                Caption(
                    value=f"📍 {item['location']}",
                    size="sm",
                    color="secondary",
                )
            )

        # Fallback: add description if no structured data
        if not item.get("price") and not item.get("specs") and item.get("description"):
            item_content.append(
                Caption(
                    value=item.get("description", ""),
                    size="sm",
                    color="secondary",
                    truncate=True,
                    maxLines=3,
                )
            )

        # Add action button if not using drilldown
        if not enable_drilldown and item.get("link_url"):
            action_type = item.get("action_type", "carousel_item_click")
            action_payload = {
                **(item.get("action_payload", {})),
                "link_url": item.get("link_url"),
                "item_id": item_id,
            }
            item_content.append(
                Button(
                    label=item.get("link_label", "View"),
                    iconEnd="external-link",
                    size="sm",
                    variant="outline",
                    block=True,
                    onClickAction=ActionConfig(
                        type=action_type, payload=action_payload, handler="client"
                    ),
                )
            )

        # Create clickable wrapper if drilldown enabled
        if enable_drilldown:
            carousel_item = Box(
                padding="xl",
                radius="xl",
                border={"size": 1, "color": {"light": "#e0e7ee", "dark": "#3f4756"}},
                background={"light": "#ffffff", "dark": "#1f2937"},
                shadow={"size": "sm", "color": {"light": "#00000010", "dark": "#00000030"}},
                minWidth=280,
                maxWidth=280,
                transition="all 0.2s ease-in-out",
                cursor="pointer",
                onClickAction=ActionConfig(
                    type="view_item_details",
                    payload={
                        "item_id": item_id,
                        "item_data": item.get("item_data", item),
                    },
                ),
                children=item_content,
            )
        else:
            carousel_item = Box(
                padding="xl",
                radius="xl",
                border={"size": 1, "color": {"light": "#e0e7ee", "dark": "#3f4756"}},
                background={"light": "#ffffff", "dark": "#1f2937"},
                shadow={"size": "sm", "color": {"light": "#00000010", "dark": "#00000030"}},
                minWidth=280,
                maxWidth=280,
                children=item_content,
            )

        carousel_items.append(carousel_item)

    # Build the carousel container
    # Wrap Row in Box with maxWidth to enable horizontal scrolling
    carousel_content = [
        Box(
            maxWidth="100%",  # Constrain width to force Row overflow
            children=[
                Row(
                    gap="xl",
                    wrap="nowrap" if scrollable else "wrap",
                    padding={"x": "lg", "y": "lg"},
                    children=carousel_items,
                )
            ],
        )
    ]

    # Add title if provided
    if title:
        carousel_content.insert(
            0,
            Text(value=title, size="xl", weight="bold", padding={"bottom": "md", "top": "sm"}),
        )

    return Card(size="lg", padding="md", children=carousel_content)


def create_property_listview(
    items: List[Dict[str, Any]],
    limit: int = 20,
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
        ...     limit=20
        ... )
    """
    list_items = []

    for item in items:
        item_id = item.get("id", "")

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


def create_detail_card(
    item_data: Dict[str, Any],
    title_key: str = "title",
    image_key: str = "image_url",
    exclude_keys: List[str] = None,
) -> Card:
    """
    Create a detailed view card for a carousel item.

    Displays all properties of an item in an organized layout with
    a close button to dismiss the details.

    Args:
        item_data: Full data dictionary for the item
        title_key: Key to use for the main title (default: "title")
        image_key: Key to use for the image (default: "image_url")
        exclude_keys: List of keys to exclude from property display

    Returns:
        Card widget with detailed item information

    Example:
        >>> detail_card = create_detail_card(
        ...     item_data={
        ...         "id": "prod_1",
        ...         "title": "Premium Headphones",
        ...         "image_url": "https://example.com/headphones.jpg",
        ...         "price": "$299.99",
        ...         "stock": 15,
        ...         "full_description": "High-quality wireless headphones...",
        ...         "rating": 4.8,
        ...         "reviews": 2847
        ...     }
        ... )
    """
    if exclude_keys is None:
        exclude_keys = ["id", "item_data", "action_type", "action_payload"]

    # Extract main fields
    item_title = item_data.get(title_key, "Item Details")
    image_url = item_data.get(image_key)

    # Build detail sections
    detail_children = []

    # Header with title and close button
    detail_children.extend(
        [
            Row(
                gap="md",
                justify="between",
                align="center",
                children=[
                    Title(value=item_title, size="2xl", weight="bold"),
                    Button(
                        label="Close",
                        iconStart="close",
                        size="sm",
                        variant="ghost",
                        onClickAction=ActionConfig(
                            type="close_details", handler="client"
                        ),
                    ),
                ],
            ),
            Divider(spacing="md"),
        ]
    )

    # Image (if available)
    if image_url:
        detail_children.append(
            Image(src=image_url, alt=item_title, height=400, fit="contain", radius="lg")
        )
        detail_children.append(Spacer(minSize="md"))

    # Full description (if available and different from short description)
    full_desc = item_data.get("full_description") or item_data.get("description")
    if full_desc:
        detail_children.extend(
            [
                Title(value="Description", size="lg", weight="semibold"),
                Text(value=full_desc, size="md", color="secondary"),
                Spacer(minSize="md"),
            ]
        )

    # Additional properties
    properties = []
    for key, value in item_data.items():
        if (
            key not in exclude_keys
            and key != title_key
            and key != image_key
            and key != "description"
            and key != "full_description"
            and value is not None
        ):
            # Format key as readable label
            label = key.replace("_", " ").title()
            properties.append((label, str(value)))

    if properties:
        detail_children.append(
            Title(value="Details", size="lg", weight="semibold")
        )

        # Display properties in a grid
        for label, value in properties:
            detail_children.append(
                Row(
                    gap="md",
                    justify="between",
                    padding={"y": "xs"},
                    children=[
                        Text(value=f"{label}:", weight="medium", color="secondary"),
                        Text(value=value, weight="semibold"),
                    ],
                )
            )

    return Card(
        size="lg",
        padding="lg",
        background={"light": "#ffffff", "dark": "#1f2937"},
        border={"size": 2, "color": {"light": "#e5e7eb", "dark": "#374151"}},
        radius="xl",
        children=detail_children,
    )


def create_yes_no_buttons(
    question: str,
    action_type: str = "user_confirmation",
    context: Dict[str, Any] = None,
    yes_label: str = "Yes",
    no_label: str = "No",
) -> Card:
    """
    Create simple yes/no buttons widget.

    Args:
        question: The question to ask the user
        action_type: The action type to send when clicked
        context: Additional context to include in the action payload
        yes_label: Label for the yes button
        no_label: Label for the no button

    Returns:
        Card widget with yes/no buttons

    Example:
        >>> widget = create_yes_no_buttons(
        ...     question="Would you like to continue?",
        ...     action_type="confirm_action",
        ...     context={"action_id": "action_123"}
        ... )
    """
    return Card(
        size="md",
        padding="md",
        children=[
            Text(value=question, size="md", weight="medium", padding={"bottom": "sm"}),
            Row(
                gap="md",
                justify="center",
                children=[
                    Button(
                        label=yes_label,
                        iconStart="check-circle",
                        color="success",
                        style="primary",
                        size="md",
                        pill=True,
                        onClickAction=ActionConfig(
                            type=action_type,
                            payload={**(context or {}), "answer": "yes"},
                        ),
                    ),
                    Button(
                        label=no_label,
                        iconStart="empty-circle",
                        color="danger",
                        style="secondary",
                        size="md",
                        pill=True,
                        onClickAction=ActionConfig(
                            type=action_type,
                            payload={**(context or {}), "answer": "no"},
                        ),
                    ),
                ],
            ),
        ],
    )


def create_image_grid(
    items: List[Dict[str, Any]], columns: int = 3, title: str = None
) -> Card:
    """
    Create a grid of images with links.

    Args:
        items: List of items with image_url, title, and link_url
        columns: Number of columns in the grid
        title: Optional title for the grid

    Returns:
        Card widget with image grid
    """
    # Group items into rows
    rows = []
    for i in range(0, len(items), columns):
        row_items = items[i : i + columns]

        row = Row(
            gap="md",
            justify="start",
            wrap="wrap",
            children=[
                Col(
                    gap="xs",
                    flex=1,
                    minWidth=150,
                    children=[
                        Image(
                            src=item["image_url"],
                            alt=item.get("title", "Image"),
                            height=150,
                            fit="cover",
                            radius="md",
                        ),
                        Text(
                            value=item["title"],
                            size="sm",
                            weight="medium",
                            truncate=True,
                        ),
                        Button(
                            label="View",
                            size="xs",
                            variant="ghost",
                            iconEnd="external-link",
                            onClickAction=ActionConfig(
                                type="open_link",
                                payload={"url": item.get("link_url")},
                                handler="client",
                            ),
                        ),
                    ],
                )
                for item in row_items
            ],
        )
        rows.append(row)

    content = rows
    if title:
        content.insert(
            0, Text(value=title, size="xl", weight="bold", padding={"bottom": "md"})
        )

    return Card(size="full", padding="lg", children=content)
