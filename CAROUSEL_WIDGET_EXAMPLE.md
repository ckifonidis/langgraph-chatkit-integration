# Image Carousel Widget - Complete Example

## Overview

This document shows how to use the custom image carousel widget in your LangGraph ChatKit integration.

## What It Does

Creates a **horizontal scrollable carousel** with:
- Images
- Titles and descriptions
- Clickable links that open in new tabs
- Responsive layout
- Support for unlimited items

## Visual Example

```
┌─────────────────────────────────────────────────────────────────┐
│  Featured Products                                               │
│                                                                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │  Image  │  │  Image  │  │  Image  │  │  Image  │  →         │
│  │         │  │         │  │         │  │         │            │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘            │
│  Product 1     Product 2     Product 3     Product 4             │
│  Great item    Amazing       Best deal    Top rated             │
│  [View →]      [View →]      [View →]      [View →]             │
└─────────────────────────────────────────────────────────────────┘
```

## Backend Implementation

### Step 1: Import the Widget Function

```python
# In backend/app/langgraph_chatkit_server.py
from .custom_widgets import create_image_carousel
```

### Step 2: Use in Your Response

```python
async def respond(
    self,
    thread: ThreadMetadata,
    item: UserMessageItem | None,
    context: dict[str, Any],
) -> AsyncIterator[ThreadStreamEvent]:

    # ... your normal response logic ...

    # Example: User asks "show me products"
    user_message = _user_message_text(item)

    if "products" in user_message.lower() or "carousel" in user_message.lower():
        # Create carousel widget
        carousel = create_image_carousel(
            title="Featured Products",
            items=[
                {
                    "id": "prod_1",
                    "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400",
                    "title": "Wireless Headphones",
                    "description": "Premium sound quality with noise cancellation",
                    "link_url": "https://example.com/products/headphones",
                    "link_label": "View Product"
                },
                {
                    "id": "prod_2",
                    "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400",
                    "title": "Smart Watch",
                    "description": "Track your fitness and stay connected",
                    "link_url": "https://example.com/products/watch",
                    "link_label": "View Product"
                },
                {
                    "id": "prod_3",
                    "image_url": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400",
                    "title": "Designer Sunglasses",
                    "description": "UV protection with style",
                    "link_url": "https://example.com/products/sunglasses",
                    "link_label": "View Product"
                },
                {
                    "id": "prod_4",
                    "image_url": "https://images.unsplash.com/photo-1491553895911-0055eca6402d?w=400",
                    "title": "Leather Sneakers",
                    "description": "Comfortable and durable",
                    "link_url": "https://example.com/products/sneakers",
                    "link_label": "View Product"
                }
            ]
        )

        # Stream the carousel as a widget item
        widget_id = _gen_id("widget")
        from chatkit.types import WidgetItem
        from datetime import datetime

        widget_item = WidgetItem(
            id=widget_id,
            thread_id=thread.id,
            created_at=datetime.now(),
            widget=carousel,
            status="completed"
        )

        yield ThreadItemDoneEvent(item=widget_item)

    # ... rest of your response logic ...
```

## Frontend (Already Configured!)

The frontend is already set up to handle carousel clicks. When a user clicks a carousel item, it will:

1. Log the action to console (in dev mode)
2. Open the link in a new tab
3. Return to the chat

The handler is in `frontend/src/components/ChatKitPanel.tsx`:

```typescript
widgets: {
  async onAction(action, widgetItem) {
    // Handle carousel item clicks
    if (action.type === "carousel_item_click" || action.type === "open_link") {
      const linkUrl = action.payload?.link_url;
      if (linkUrl) {
        window.open(linkUrl, "_blank", "noopener,noreferrer");
        return;
      }
    }
  }
}
```

## Complete Working Example

Here's a complete example you can add to your backend to test the carousel:

```python
# backend/app/langgraph_chatkit_server.py

from .custom_widgets import create_image_carousel, create_yes_no_buttons
from chatkit.types import WidgetItem
from chatkit.server import ThreadItemDoneEvent
from datetime import datetime

class LangGraphChatKitServer(ChatKitServer[dict[str, Any]]):

    # ... existing code ...

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:

        # ... existing code to get user_message ...

        user_message = _user_message_text(item)

        # Check if user wants to see carousel
        if "show" in user_message.lower() and "carousel" in user_message.lower():
            # Yield a text response first
            text_msg_id = _gen_id("msg")
            text_item = AssistantMessageItem(
                id=text_msg_id,
                thread_id=thread.id,
                created_at=datetime.now(),
                content=[AssistantMessageContent(
                    text="Here are some featured items:"
                )],
                status="completed"
            )
            yield ThreadItemDoneEvent(item=text_item)

            # Then yield the carousel widget
            carousel = create_image_carousel(
                title="Featured Collection",
                items=[
                    {
                        "id": "item_1",
                        "image_url": "https://picsum.photos/400/300?random=1",
                        "title": "Mountain Landscape",
                        "description": "Beautiful mountain scenery",
                        "link_url": "https://unsplash.com/photos/mountains",
                        "link_label": "View Full Size"
                    },
                    {
                        "id": "item_2",
                        "image_url": "https://picsum.photos/400/300?random=2",
                        "title": "Ocean Sunset",
                        "description": "Stunning sunset over the ocean",
                        "link_url": "https://unsplash.com/photos/ocean",
                        "link_label": "View Full Size"
                    },
                    {
                        "id": "item_3",
                        "image_url": "https://picsum.photos/400/300?random=3",
                        "title": "City Lights",
                        "description": "Urban nighttime photography",
                        "link_url": "https://unsplash.com/photos/city",
                        "link_label": "View Full Size"
                    },
                    {
                        "id": "item_4",
                        "image_url": "https://picsum.photos/400/300?random=4",
                        "title": "Forest Path",
                        "description": "Peaceful forest trail",
                        "link_url": "https://unsplash.com/photos/forest",
                        "link_label": "View Full Size"
                    }
                ]
            )

            widget_id = _gen_id("widget")
            widget_item = WidgetItem(
                id=widget_id,
                thread_id=thread.id,
                created_at=datetime.now(),
                widget=carousel,
                status="completed"
            )

            yield ThreadItemDoneEvent(item=widget_item)
            return

        # ... rest of your normal response logic ...
```

## Customization Options

### Change Number of Items

```python
# Show 2 items
carousel = create_image_carousel(
    items=my_items[:2]
)

# Show 10 items (will scroll)
carousel = create_image_carousel(
    items=my_items[:10]
)
```

### No Title

```python
carousel = create_image_carousel(
    title=None,  # or omit the parameter
    items=[...]
)
```

### Custom Action Types

```python
items=[
    {
        "image_url": "...",
        "title": "Special Item",
        "action_type": "special_action",  # Custom action type
        "action_payload": {
            "custom_data": "value",
            "item_id": 123
        }
    }
]
```

Then handle in frontend:

```typescript
widgets: {
  async onAction(action) {
    if (action.type === "special_action") {
      console.log("Special action triggered:", action.payload);
      // Do something special
    }
  }
}
```

### Dynamic Data from API

```python
# Fetch products from your database/API
async def get_featured_products():
    # Your logic to fetch products
    products = await db.query("SELECT * FROM products WHERE featured = true")
    return products

# In respond():
products = await get_featured_products()

carousel = create_image_carousel(
    title="Today's Featured Products",
    items=[
        {
            "id": prod.id,
            "image_url": prod.image_url,
            "title": prod.name,
            "description": f"${prod.price} - {prod.short_description}",
            "link_url": f"https://yoursite.com/products/{prod.id}",
            "link_label": "Buy Now"
        }
        for prod in products
    ]
)
```

## Testing the Carousel

### 1. Start Your Application

```bash
# Make sure both frontend and backend are running
npm start
```

### 2. Send a Test Message

In the ChatKit UI, type:
```
show me a carousel
```

or

```
show me products
```

### 3. Interact with the Carousel

- Scroll horizontally through items
- Click "View" button on any item
- Link should open in new tab

## Advanced Example: Interactive Carousel with Selection

```python
# backend/app/custom_widgets.py

def create_selectable_carousel(
    items: List[Dict[str, Any]],
    title: str = None,
    selection_action: str = "item_selected"
) -> Card:
    """Carousel where clicking an item selects it (instead of opening link)."""

    carousel_items = []

    for item in items:
        carousel_item = Col(
            gap="sm",
            minWidth=200,
            maxWidth=200,
            children=[
                # Entire item is clickable
                Box(
                    padding="sm",
                    radius="lg",
                    border={"size": 2, "color": "primary"},
                    background={"light": "#ffffff", "dark": "#1f2937"},
                    children=[
                        Image(
                            src=item["image_url"],
                            alt=item["title"],
                            height=150,
                            fit="cover",
                            radius="md"
                        ),
                        Text(value=item["title"], weight="semibold", size="md"),
                        *(
                            [Caption(value=item["price"], color="success")]
                            if item.get("price")
                            else []
                        )
                    ]
                ),
                # Selection button
                Button(
                    label=item.get("button_label", "Select"),
                    color="primary",
                    block=True,
                    onClickAction=ActionConfig(
                        type=selection_action,
                        payload={
                            "item_id": item["id"],
                            "item_data": item
                        }
                    )
                )
            ]
        )
        carousel_items.append(carousel_item)

    content = [
        Row(
            gap="md",
            wrap="nowrap",
            padding="sm",
            children=carousel_items
        )
    ]

    if title:
        content.insert(0, Text(value=title, size="xl", weight="bold"))

    return Card(size="full", padding="lg", children=content)
```

## Integration with LangGraph Responses

```python
# When LangGraph returns a response that should show products
async def respond(...):

    # Stream from LangGraph API
    async for event in self.langgraph_client.stream_response(
        thread_id=langgraph_thread_id,
        user_message=user_message,
    ):
        ai_msg = self.langgraph_client.extract_latest_ai_message(event)
        # ... existing logic ...

    # After the AI response, check if we should add a carousel
    if ai_msg:
        ai_content = ai_msg.get("content", "")

        # Yield the AI message first
        yield ThreadItemDoneEvent(item=ai_message_item)

        # Then check if we should add a carousel
        if "products" in user_message.lower():
            # Fetch and show product carousel
            carousel = create_image_carousel(
                title="Recommended Products",
                items=await fetch_recommended_products()
            )

            widget_item = WidgetItem(
                id=_gen_id("widget"),
                thread_id=thread.id,
                created_at=datetime.now(),
                widget=carousel,
                status="completed"
            )

            yield ThreadItemDoneEvent(item=widget_item)
```

## Real-World Use Cases

### 1. E-Commerce Product Recommendations

```python
carousel = create_image_carousel(
    title="You might also like",
    items=[
        {
            "image_url": product.image,
            "title": product.name,
            "description": f"${product.price} - {product.rating}⭐",
            "link_url": f"/products/{product.id}"
        }
        for product in recommended_products
    ]
)
```

### 2. Article/Blog Post Carousel

```python
carousel = create_image_carousel(
    title="Related Articles",
    items=[
        {
            "image_url": article.cover_image,
            "title": article.title,
            "description": f"{article.read_time} min read • {article.author}",
            "link_url": article.url,
            "link_label": "Read More"
        }
        for article in related_articles
    ]
)
```

### 3. Image Gallery

```python
carousel = create_image_carousel(
    title="Photo Gallery",
    items=[
        {
            "image_url": photo.thumbnail_url,
            "title": photo.caption,
            "description": f"Taken on {photo.date}",
            "link_url": photo.full_size_url,
            "link_label": "View Full Size"
        }
        for photo in gallery_photos
    ]
)
```

### 4. Video Thumbnails

```python
carousel = create_image_carousel(
    title="Watch These Videos",
    items=[
        {
            "image_url": video.thumbnail,
            "title": video.title,
            "description": f"{video.duration} • {video.views} views",
            "link_url": video.watch_url,
            "link_label": "Watch Now"
        }
        for video in videos
    ]
)
```

## Complete Integration Example

Here's a full example showing how to integrate the carousel into your ChatKit server:

```python
# backend/app/langgraph_chatkit_server.py

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from typing import Any, AsyncIterator
from uuid import uuid4

from chatkit.server import ChatKitServer, ThreadItemDoneEvent
from chatkit.types import (
    AssistantMessageContent,
    AssistantMessageItem,
    ThreadItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
    WidgetItem,
)

from .langgraph_client import LangGraphStreamClient
from .memory_store import MemoryStore
from .custom_widgets import create_image_carousel, create_yes_no_buttons

logger = logging.getLogger(__name__)


def _gen_id(prefix: str) -> str:
    """Generate a unique ID with a prefix."""
    return f"{prefix}_{uuid4().hex[:8]}"


def _user_message_text(item: UserMessageItem) -> str:
    """Extract text content from a user message item."""
    parts: list[str] = []
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()


class LangGraphChatKitServer(ChatKitServer[dict[str, Any]]):
    """ChatKit server with LangGraph and custom widgets."""

    def __init__(
        self,
        langgraph_url: str | None = None,
        assistant_id: str | None = None,
    ) -> None:
        self.store: MemoryStore = MemoryStore()
        super().__init__(self.store)

        self.langgraph_url = langgraph_url or os.getenv(
            "LANGGRAPH_API_URL",
            "https://nbg-webapp-cc-lg-test-we-dev-01-axhqfbexe3eeerbn.westeurope-01.azurewebsites.net",
        )
        self.assistant_id = assistant_id or os.getenv("LANGGRAPH_ASSISTANT_ID", "agent")

        self.langgraph_client = LangGraphStreamClient(
            base_url=self.langgraph_url,
            assistant_id=self.assistant_id,
        )

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:

        if item is None:
            return

        user_message = _user_message_text(item)
        if not user_message:
            return

        logger.info(f"Processing message for thread {thread.id}")

        # Check for carousel trigger
        if "carousel" in user_message.lower() or "show me products" in user_message.lower():
            # Show text response
            text_item = AssistantMessageItem(
                id=_gen_id("msg"),
                thread_id=thread.id,
                created_at=datetime.now(),
                content=[AssistantMessageContent(
                    text="Here's a carousel of featured items:"
                )],
                status="completed"
            )
            yield ThreadItemDoneEvent(item=text_item)

            # Show carousel widget
            carousel = create_image_carousel(
                title="Featured Items",
                items=[
                    {
                        "id": f"item_{i}",
                        "image_url": f"https://picsum.photos/400/300?random={i}",
                        "title": f"Item {i}",
                        "description": f"This is item number {i}",
                        "link_url": f"https://example.com/item/{i}",
                    }
                    for i in range(1, 6)
                ]
            )

            widget_item = WidgetItem(
                id=_gen_id("widget"),
                thread_id=thread.id,
                created_at=datetime.now(),
                widget=carousel,
                status="completed"
            )

            yield ThreadItemDoneEvent(item=widget_item)
            return

        # ... rest of your normal LangGraph response logic ...
```

## Styling the Carousel

The carousel uses ChatKit's theme-aware colors, so it automatically adapts to light/dark mode!

**In Light Mode:**
- White background
- Light gray borders
- Black text

**In Dark Mode:**
- Dark background
- Darker borders
- White text

## Troubleshooting

### Images Not Loading

If images don't display:
1. Check image URLs are publicly accessible
2. Verify CORS headers allow the images
3. Use HTTPS URLs (not HTTP)

### Links Not Opening

If links don't work:
1. Check console for errors
2. Verify `link_url` is in the payload
3. Check browser pop-up blocker settings

### Carousel Not Scrolling

The carousel should scroll horizontally automatically. If not:
1. Check that `wrap="nowrap"` is set on the Row
2. Verify each item has `minWidth` set
3. Check parent container allows overflow

## API Reference

### create_image_carousel()

```python
def create_image_carousel(
    items: List[Dict[str, Any]],
    title: str = None,
    scrollable: bool = True,
) -> Card
```

**Parameters:**

- `items` (List[Dict]): List of carousel items
  - `image_url` (str, required): URL of the image
  - `title` (str, required): Title text
  - `description` (str, optional): Description text
  - `link_url` (str, optional): URL to open on click
  - `link_label` (str, optional): Button label (default: "View")
  - `id` (str, optional): Unique identifier
  - `action_type` (str, optional): Custom action type
  - `action_payload` (dict, optional): Additional payload data

- `title` (str, optional): Carousel heading
- `scrollable` (bool, optional): Enable horizontal scrolling (default: True)

**Returns:** `Card` widget

## Next Steps

1. **Test the carousel** - Try "show me a carousel" in the chat
2. **Customize for your use case** - Modify the example for your products/content
3. **Add more widget types** - Check `custom_widgets.py` for yes/no buttons and more
4. **Create your own compositions** - Use the guide to build custom widgets

## Files Modified

1. ✅ `backend/app/custom_widgets.py` - Widget library created
2. ✅ `frontend/src/components/ChatKitPanel.tsx` - Action handler added
3. ✅ `CAROUSEL_WIDGET_EXAMPLE.md` - This documentation

All ready to use! Just import and call `create_image_carousel()` in your backend response.
