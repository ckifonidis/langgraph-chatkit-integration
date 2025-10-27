"""
Custom Widget Library for LangGraph ChatKit Integration.

This module provides reusable widget compositions for common UI patterns.
"""

from typing import List, Dict, Any
from chatkit.widgets import Card, Row, Col, Image, Text, Button, Caption, Box
from chatkit.actions import ActionConfig


def create_image_carousel(
    items: List[Dict[str, Any]],
    title: str = None,
    scrollable: bool = True,
) -> Card:
    """
    Create a horizontal carousel of images with links.

    Each item should have:
    - image_url: URL of the image to display
    - title: Title text below the image
    - description: Optional description text
    - link_url: Optional URL to open when clicked
    - action_type: Optional custom action type (defaults to "open_link")
    - action_payload: Optional additional payload data

    Args:
        items: List of carousel items with image, title, link
        title: Optional title for the carousel
        scrollable: Whether the carousel should scroll horizontally

    Returns:
        Card widget with horizontal scrollable carousel

    Example:
        >>> carousel = create_image_carousel(
        ...     title="Featured Products",
        ...     items=[
        ...         {
        ...             "image_url": "https://example.com/product1.jpg",
        ...             "title": "Product 1",
        ...             "description": "Amazing product",
        ...             "link_url": "https://example.com/product1"
        ...         },
        ...         {
        ...             "image_url": "https://example.com/product2.jpg",
        ...             "title": "Product 2",
        ...             "description": "Another great product",
        ...             "link_url": "https://example.com/product2"
        ...         }
        ...     ]
        ... )
    """
    carousel_items = []

    for item in items:
        # Create action config
        action_type = item.get("action_type", "carousel_item_click")
        action_payload = {
            **(item.get("action_payload", {})),
            "link_url": item.get("link_url"),
            "item_id": item.get("id", item["title"]),
        }

        # Create a column for each carousel item
        carousel_item = Col(
            gap="sm",
            minWidth=220,  # Fixed width for each item
            maxWidth=220,
            children=[
                # Image with clickable overlay
                Box(
                    padding=0,
                    radius="lg",
                    border={"size": 1, "color": {"light": "#e5e7eb", "dark": "#374151"}},
                    background={"light": "#ffffff", "dark": "#1f2937"},
                    children=[
                        Image(
                            src=item["image_url"],
                            alt=item.get("title", "Image"),
                            height=180,
                            fit="cover",
                            radius="md",
                            flush=True,
                        )
                    ],
                ),
                # Title
                Text(
                    value=item["title"],
                    size="md",
                    weight="semibold",
                    truncate=True,
                    maxLines=2,
                ),
                # Description (if provided)
                *(
                    [
                        Caption(
                            value=item["description"],
                            size="sm",
                            color="secondary",
                            truncate=True,
                            maxLines=2,
                        )
                    ]
                    if item.get("description")
                    else []
                ),
                # Link button
                Button(
                    label=item.get("link_label", "View"),
                    iconEnd="external-link",
                    size="sm",
                    variant="outline",
                    block=True,
                    onClickAction=ActionConfig(
                        type=action_type, payload=action_payload, handler="client"
                    ),
                ),
            ],
        )

        carousel_items.append(carousel_item)

    # Build the carousel container
    # Wrap Row in Box with maxWidth to enable horizontal scrolling
    carousel_content = [
        Box(
            maxWidth="100%",  # Constrain width to force Row overflow
            children=[
                Row(
                    gap="md",
                    wrap="nowrap" if scrollable else "wrap",
                    padding={"x": "sm", "y": "sm"},
                    children=carousel_items,
                )
            ],
        )
    ]

    # Add title if provided
    if title:
        carousel_content.insert(
            0,
            Text(value=title, size="lg", weight="bold", padding={"bottom": "sm"}),
        )

    return Card(size="lg", padding="md", children=carousel_content)


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
