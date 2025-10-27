# Drilldown Carousel Usage Guide

## Overview

The drilldown carousel allows users to click on carousel items to view detailed information. This guide shows how to implement it in your backend.

## Quick Start

### Step 1: Create a Drilldown Carousel

```python
from backend.examples.widget_examples import get_example_widget
from chatkit.types import WidgetItem
from chatkit.server import ThreadItemDoneEvent
from datetime import datetime

# In your respond() method:
carousel = get_example_widget("products_drilldown")

widget_item = WidgetItem(
    id=_gen_id("widget"),
    thread_id=thread.id,
    created_at=datetime.now(),
    widget=carousel,
    status="completed"
)

yield ThreadItemDoneEvent(item=widget_item)
```

### Step 2: Handle the Drilldown Action

When a user clicks a carousel item with `enable_drilldown=True`, the backend receives a `view_item_details` action.

```python
from backend.examples.custom_widgets import create_detail_card
from chatkit.types import Action, WidgetItem, AssistantMessageItem, AssistantMessageContent
from chatkit.server import ThreadItemDoneEvent, ThreadStreamEvent
from typing import AsyncIterator

async def action(
    self,
    thread: ThreadMetadata,
    action: Action[str, Any],
    sender: WidgetItem | None,
    context: dict[str, Any],
) -> AsyncIterator[ThreadStreamEvent]:
    """Handle widget actions."""

    # Handle drilldown action
    if action.type == "view_item_details":
        item_data = action.payload.get("item_data", {})

        # Create detail card widget
        detail_widget = create_detail_card(item_data)

        # Send as new widget item
        yield ThreadItemDoneEvent(
            item=WidgetItem(
                id=_gen_id("widget"),
                thread_id=thread.id,
                created_at=datetime.now(),
                widget=detail_widget,
                status="completed"
            )
        )
```

### Step 3: Handle Close Action (Optional Client-Side)

The detail card has a "Close" button. You can handle it client-side in the frontend:

```typescript
// In frontend/src/components/ChatKitPanel.tsx
widgets: {
  async onAction(action, widgetItem) {
    if (action.type === "close_details") {
      // The widget will automatically be removed from view
      console.log("Details closed");
      return { success: true };
    }
  }
}
```

## Complete Example

### Backend Implementation

```python
# In your ChatKitServer class (e.g., langgraph_chatkit_server.py)

from backend.examples.custom_widgets import (
    create_image_carousel,
    create_detail_card
)
from backend.examples.widget_examples import PRODUCT_DRILLDOWN_CAROUSEL

class LangGraphChatKitServer(ChatKitServer[dict[str, Any]]):

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:

        user_message = _user_message_text(item)

        # Check for carousel trigger
        if "show products" in user_message.lower():
            # Show text response
            text_item = AssistantMessageItem(
                id=_gen_id("msg"),
                thread_id=thread.id,
                created_at=datetime.now(),
                content=[AssistantMessageContent(
                    text="Here are our featured products. Click any item to see full details:"
                )],
                status="completed"
            )
            yield ThreadItemDoneEvent(item=text_item)

            # Show drilldown carousel
            carousel = PRODUCT_DRILLDOWN_CAROUSEL

            widget_item = WidgetItem(
                id=_gen_id("widget"),
                thread_id=thread.id,
                created_at=datetime.now(),
                widget=carousel,
                status="completed"
            )

            yield ThreadItemDoneEvent(item=widget_item)
            return

        # ... rest of your logic

    async def action(
        self,
        thread: ThreadMetadata,
        action: Action[str, Any],
        sender: WidgetItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:

        # Handle drilldown
        if action.type == "view_item_details":
            item_data = action.payload.get("item_data", {})

            # Create detail card
            detail_widget = create_detail_card(item_data)

            # Send detail widget
            yield ThreadItemDoneEvent(
                item=WidgetItem(
                    id=_gen_id("widget"),
                    thread_id=thread.id,
                    created_at=datetime.now(),
                    widget=detail_widget,
                    status="completed"
                )
            )
```

## Creating Custom Drilldown Carousels

### Example with Dynamic Data

```python
# Fetch products from database
products = await fetch_products_from_db()

# Create carousel with drilldown
carousel = create_image_carousel(
    title="Available Products",
    items=[
        {
            "id": str(product.id),
            "image_url": product.thumbnail_url,
            "title": product.name,
            "description": product.short_description,
            "item_data": {
                "title": product.name,
                "image_url": product.full_image_url,
                "price": f"${product.price:.2f}",
                "stock": product.stock_quantity,
                "rating": product.average_rating,
                "reviews": product.review_count,
                "brand": product.brand,
                "category": product.category,
                "full_description": product.full_description,
                # Add any other properties you want to display
                "sku": product.sku,
                "weight": f"{product.weight}kg",
                "dimensions": product.dimensions,
            }
        }
        for product in products
    ],
    enable_drilldown=True,
    scrollable=True
)
```

## Customizing the Detail Card

You can customize which properties appear in the detail card:

```python
# Exclude certain keys from display
detail_widget = create_detail_card(
    item_data=item_data,
    title_key="title",  # Which field to use as the main title
    image_key="image_url",  # Which field to use as the image
    exclude_keys=["id", "thumbnail_url", "internal_notes"]  # Don't show these
)
```

## User Flow

1. **User sees carousel** with summary information (image, title, short description)
2. **User clicks item** → Sends `view_item_details` action to backend
3. **Backend responds** with detailed widget showing all properties
4. **User views details** → Large image, full description, all product properties
5. **User clicks Close** → Detail card dismissed (handled client-side)
6. **Carousel remains** visible for browsing other items

## Benefits

- ✅ **Clean UI** - Carousel shows minimal info, details on demand
- ✅ **Expandable** - Easily show unlimited properties in detail view
- ✅ **Flexible** - Works with any type of data (products, articles, users, etc.)
- ✅ **Server-controlled** - Backend decides what details to show
- ✅ **Horizontal scrolling** - Carousel scrolls smoothly with many items
- ✅ **No page navigation** - Everything happens within the chat interface

## Testing

Try these prompts in your chat interface:

```
show products
show me a carousel
show products with details
```

Then click on any item to see the drilldown behavior!
