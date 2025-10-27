# Quick Start: Image Carousel Widget

## 🎯 What You Have

✅ **Custom carousel widget function** - `create_image_carousel()`
✅ **Frontend handler configured** - Clicks open links in new tabs
✅ **Example widgets ready** - Products, blog posts, gallery
✅ **Full documentation** - Complete usage guide

## 🚀 Quick Test (3 Steps)

### Step 1: Add Import to Your Server

```python
# backend/app/langgraph_chatkit_server.py

# Add these imports at the top
from .widget_examples import get_example_widget
from chatkit.types import WidgetItem
```

### Step 2: Add Widget Logic to respond()

```python
# In your respond() method, add this check:

user_message = _user_message_text(item)

# Check for carousel trigger keywords
if "carousel" in user_message.lower() or "products" in user_message.lower():
    # Show text first
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
    widget = get_example_widget("products")  # or "blog", "gallery", "yes_no"

    widget_item = WidgetItem(
        id=_gen_id("widget"),
        thread_id=thread.id,
        created_at=datetime.now(),
        widget=widget,
        status="completed"
    )

    yield ThreadItemDoneEvent(item=widget_item)
    return

# ... rest of your normal logic ...
```

### Step 3: Test It!

1. Make sure your app is running:
   ```bash
   npm start
   ```

2. In the chat, type:
   ```
   show me a carousel
   ```
   or
   ```
   show me products
   ```

3. You should see:
   - A horizontal scrollable carousel
   - Images with titles and descriptions
   - "Shop Now" or "View" buttons
   - Clicking opens links in new tabs

## 📝 Full Files Created

1. **`backend/app/custom_widgets.py`**
   - `create_image_carousel()` - Main carousel function
   - `create_yes_no_buttons()` - Simple yes/no widget
   - `create_image_grid()` - Grid layout alternative

2. **`backend/app/widget_examples.py`**
   - Pre-built carousel examples
   - `get_example_widget()` - Helper to get examples
   - Ready-to-use product, blog, and gallery carousels

3. **`frontend/src/components/ChatKitPanel.tsx`** (Updated)
   - Added `widgets.onAction` handler
   - Handles carousel clicks
   - Opens links in new tabs

4. **Documentation**
   - `HOW_WIDGETS_WORK.md` - Complete widget guide
   - `CUSTOM_WIDGETS_GUIDE.md` - Custom widget patterns
   - `CAROUSEL_WIDGET_EXAMPLE.md` - Detailed carousel docs
   - `QUICK_START_CAROUSEL.md` - This quick start

## 🎨 Customizing the Carousel

### Use Your Own Data

```python
from .custom_widgets import create_image_carousel

# Fetch from database
products = await db.query("SELECT * FROM products WHERE featured = true LIMIT 5")

carousel = create_image_carousel(
    title="Today's Deals",
    items=[
        {
            "id": str(prod.id),
            "image_url": prod.image_url,
            "title": prod.name,
            "description": f"${prod.price} - {prod.rating}⭐",
            "link_url": f"https://yoursite.com/products/{prod.id}",
            "link_label": "Buy Now"
        }
        for prod in products
    ]
)
```

### Change Styling

The carousel automatically adapts to your ChatKit theme (light/dark mode). Each item is:
- **220px wide** (fixed for consistent layout)
- **180px tall** images
- **Scrollable** horizontally
- **Bordered** cards with rounded corners

### Add Custom Actions

Instead of opening links, you can trigger custom backend actions:

```python
carousel = create_image_carousel(
    items=[
        {
            "image_url": "...",
            "title": "Item 1",
            "action_type": "select_product",  # Custom action
            "action_payload": {"product_id": 123},  # Custom data
            # Don't include link_url to prevent opening links
        }
    ]
)
```

Then handle on backend:

```python
# In your ChatKitServer
async def action(self, thread, action, sender, context):
    if action.type == "select_product":
        product_id = action.payload["product_id"]
        # Do something with the product
        yield ThreadItemDoneEvent(...)
```

## 🔧 Available Widget Examples

Call `get_example_widget()` with these names:

| Name | Description |
|------|-------------|
| `"products"` | E-commerce product carousel |
| `"blog"` | Blog post carousel with read more links |
| `"gallery"` | Photo gallery with full-size links |
| `"yes_no"` | Simple yes/no confirmation buttons |

## ⚡ Next Steps

1. **Test the carousel** - Try it in your running app
2. **Customize the data** - Replace example data with your real content
3. **Try yes/no buttons** - Use `create_yes_no_buttons()` for confirmations
4. **Create more widgets** - Use the patterns in `custom_widgets.py`
5. **Read full docs** - Check `HOW_WIDGETS_WORK.md` for all widget types

## 💡 Tips

- **Images load from external URLs** - Make sure they're publicly accessible
- **Links open in new tabs** - Configured with `noopener,noreferrer` for security
- **Responsive** - Works on mobile and desktop
- **Theme-aware** - Automatically adjusts to light/dark mode
- **Scrollable** - Carousel scrolls horizontally on overflow

## 🎉 You're Ready!

Your carousel widget is fully implemented and ready to use. Just add the trigger logic to your backend response and test it out!

**Need help?** Check the other documentation files for more details and examples.
