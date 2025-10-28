# Custom Components - Rule-Based Widget System

## Overview

The `custom_components` directory provides a **rule-based system** for automatically rendering ChatKit widgets based on LangGraph response data.

Components define:
1. **Rules** - When to activate (based on response data)
2. **Rendering** - How to create the widget

## Architecture

```
LangGraph Response → Component Registry → Matching Components → Widgets → ChatKit UI
       ↓                      ↓                    ↓                ↓
   {query_results}     check_rules()         render()         Carousel
   {sql_query}         PropertyCarousel      PropertyDetail   DetailCard
   {messages}          [...]                 [...]            [...]
```

## Quick Start

### 1. Create a Component

```python
# custom_components/my_component.py
from .base import CustomComponent
from chatkit.widgets import Card, Text

class MyComponent(CustomComponent):
    def check_rules(self, response_data: dict) -> bool:
        """Return True if this component should render."""
        return "special_field" in response_data

    def render(self, response_data: dict) -> Card:
        """Create the widget."""
        data = response_data["special_field"]
        return Card(children=[
            Text(value=f"Special: {data}")
        ])
```

### 2. Register the Component

```python
# In backend/app/main.py
from custom_components import ComponentRegistry
from custom_components.my_component import MyComponent

registry = ComponentRegistry()
registry.register(MyComponent())

server = create_server_from_env(component_registry=registry)
```

### 3. Components Activate Automatically

When LangGraph returns a response with `special_field`, your component will:
1. ✅ Check rules → `check_rules()` returns True
2. ✅ Render widget → `render()` creates Card
3. ✅ Display in UI → Widget appears in chat

## Built-In Components

### PropertyCarouselComponent

**Purpose**: Display property search results as a scrollable carousel

**Rules**: Activates when `query_results` exists and has items

**Rendering**:
- Horizontal scrollable carousel
- Shows first 20 properties (configurable)
- Each item shows: image, title, price, area, rooms, location
- Click to view full details (drilldown enabled)

**Usage**:
```python
registry.register(PropertyCarouselComponent(max_items=20))
```

**LangGraph Response Example**:
```json
{
  "query_results": [
    {
      "code": "00001655",
      "title": "House 192sqm, Zefiri",
      "price": 125000,
      "propertyArea": 192,
      "numberOfRooms": 4,
      "defaultImagePath": "https://...",
      "address": {"prefecture": "Zefiri"}
    }
  ]
}
```

**Rendered Widget**: Carousel with property cards

### PropertyDetailComponent

**Purpose**: Show full property details when user clicks a carousel item

**Activation**: Via `view_item_details` action (triggered by carousel click)

**Rendering**:
- Large property image
- Title and property code
- Price and key specs (highlighted)
- Full description
- Amenities (as badges)
- Location details
- Property specifications
- Close button

**Usage**: Automatically handled in `LangGraphChatKitServer.action()` method

## Creating Custom Components

### Step 1: Inherit from CustomComponent

```python
from custom_components.base import CustomComponent
from chatkit.widgets import Card
from typing import Any

class MyCustomComponent(CustomComponent):
    def __init__(self, config: dict = None):
        self.config = config or {}

    def check_rules(self, response_data: dict[str, Any]) -> bool:
        # Define when this component should activate
        return True  # Your logic here

    def render(self, response_data: dict[str, Any]) -> Card | None:
        # Create and return your widget
        return Card(children=[...])

    def get_priority(self) -> int:
        # Lower number = higher priority (default: 100)
        return 50
```

### Step 2: Implement Rules

Rules determine **when** your component activates:

**Simple rule:**
```python
def check_rules(self, response_data):
    return "user_data" in response_data
```

**Complex rule:**
```python
def check_rules(self, response_data):
    # Check multiple conditions
    has_results = len(response_data.get("results", [])) > 0
    is_type_user = response_data.get("type") == "user_search"
    return has_results and is_type_user
```

**Nested data rule:**
```python
def check_rules(self, response_data):
    messages = response_data.get("messages", [])
    # Check if last AI message mentions "booking"
    if messages:
        last_msg = messages[-1]
        if last_msg.get("type") == "ai":
            return "booking" in last_msg.get("content", "").lower()
    return False
```

### Step 3: Implement Rendering

Create ChatKit widgets from response data:

```python
from chatkit.widgets import Card, Title, Row, Button, Text
from chatkit.actions import ActionConfig

def render(self, response_data):
    results = response_data.get("results", [])

    return Card(
        size="lg",
        padding="md",
        children=[
            Title(value=f"Found {len(results)} Results"),
            Row(
                gap="sm",
                children=[
                    Button(
                        label=item["name"],
                        onClickAction=ActionConfig(
                            type="select_item",
                            payload={"id": item["id"]}
                        )
                    )
                    for item in results[:5]
                ]
            )
        ]
    )
```

### Step 4: Handle Priority

Control render order with priority (lower = earlier):

```python
def get_priority(self) -> int:
    return 10   # Very high priority
    return 50   # Medium priority
    return 100  # Default priority
    return 200  # Low priority
```

**Example**: Show text summary (priority 10) before carousel (priority 50)

## Component Registry

### Registration

```python
registry = ComponentRegistry()

# Register multiple components
registry.register(PropertyCarouselComponent())
registry.register(UserProfileComponent())
registry.register(SummaryTextComponent())

# Components execute in priority order
```

### Execution

The registry automatically:
1. Checks each component's rules in priority order
2. Renders widgets for components that match
3. Returns list of widgets to display
4. Logs component execution for debugging

```python
# In LangGraphChatKitServer
widgets = registry.get_widgets(langgraph_response)
# widgets = [Carousel, UserProfile, Summary]

for widget in widgets:
    yield ThreadItemDoneEvent(item=WidgetItem(..., widget=widget))
```

## Advanced Patterns

### Conditional Rendering

```python
class ConditionalComponent(CustomComponent):
    def __init__(self, condition_fn):
        self.condition_fn = condition_fn

    def check_rules(self, response_data):
        return self.condition_fn(response_data)

    def render(self, response_data):
        return Card(children=[...])

# Usage
registry.register(
    ConditionalComponent(
        condition_fn=lambda r: r.get("status") == "success"
    )
)
```

### Parameterized Components

```python
class CounterComponent(CustomComponent):
    def __init__(self, threshold: int = 10):
        self.threshold = threshold

    def check_rules(self, response_data):
        count = response_data.get("count", 0)
        return count >= self.threshold

    def render(self, response_data):
        count = response_data["count"]
        return Card(children=[
            Text(value=f"High count detected: {count}")
        ])

# Register with custom threshold
registry.register(CounterComponent(threshold=50))
```

### Multi-Widget Components

A single component can return multiple related widgets:

```python
def render(self, response_data):
    # Return a list of widgets (not currently supported by base class)
    # But you can register multiple components with related rules
    pass
```

## Best Practices

### 1. Single Responsibility

Each component should handle **one specific widget type**:

```python
# Good ✓
PropertyCarouselComponent  # Shows property results
PropertyDetailComponent    # Shows property details

# Bad ✗
PropertyComponent  # Tries to do both
```

### 2. Defensive Programming

Handle missing data gracefully:

```python
def render(self, response_data):
    try:
        data = response_data.get("results", [])
        if not data:
            return None  # Skip rendering

        return Card(children=[...])

    except Exception as e:
        logger.error(f"Render failed: {e}")
        return None  # Don't crash
```

### 3. Clear Rule Logic

Make rules easy to understand:

```python
# Good ✓
def check_rules(self, response_data):
    has_properties = len(response_data.get("query_results", [])) > 0
    is_property_search = response_data.get("sql_query", {}).get("type") == "Apartment"
    return has_properties and is_property_search

# Bad ✗
def check_rules(self, response_data):
    return (r:=response_data.get("q",[])) and len(r)>0 and r[0].get("t")=="A"
```

### 4. Logging

Log important events for debugging:

```python
def render(self, response_data):
    logger.info(f"Rendering carousel with {len(items)} items")
    return Card(...)
```

## Troubleshooting

### Component Not Rendering

**Problem**: Component rules match but widget doesn't appear

**Solutions**:
1. Check `check_rules()` returns `True`
2. Verify `render()` doesn't return `None`
3. Check logs for exceptions
4. Ensure component is registered

### Multiple Components Rendering

**Problem**: Too many widgets appear

**Solutions**:
1. Make rules more specific
2. Adjust component priorities
3. Remove conflicting components from registry

### Component Order Wrong

**Problem**: Widgets appear in wrong order

**Solutions**:
1. Set `get_priority()` on components
2. Lower number = renders first
3. Check registration order (tie-breaker)

## Example: Complete Custom Component

```python
# custom_components/booking_confirmation.py
from .base import CustomComponent
from chatkit.widgets import Card, Title, Text, Row, Button, Divider
from chatkit.actions import ActionConfig

class BookingConfirmationComponent(CustomComponent):
    """Show booking confirmation when LangGraph returns booking data."""

    def check_rules(self, response_data):
        # Activate if we have booking data
        booking = response_data.get("booking_data")
        return booking is not None and booking.get("status") == "pending"

    def render(self, response_data):
        booking = response_data["booking_data"]

        return Card(
            size="lg",
            padding="lg",
            children=[
                Title(value="Confirm Your Booking", size="xl"),
                Divider(),
                Text(value=f"Service: {booking['service']}"),
                Text(value=f"Date: {booking['date']}"),
                Text(value=f"Time: {booking['time']}"),
                Text(value=f"Price: €{booking['price']}"),
                Divider(),
                Row(
                    gap="md",
                    justify="end",
                    children=[
                        Button(
                            label="Cancel",
                            style="secondary",
                            onClickAction=ActionConfig(
                                type="cancel_booking",
                                payload={"booking_id": booking["id"]}
                            )
                        ),
                        Button(
                            label="Confirm",
                            style="primary",
                            color="success",
                            onClickAction=ActionConfig(
                                type="confirm_booking",
                                payload={"booking_id": booking["id"]}
                            )
                        )
                    ]
                )
            ]
        )

    def get_priority(self):
        return 10  # High priority - show before other widgets

# Register it
registry.register(BookingConfirmationComponent())
```

## Testing Components

Test components in isolation:

```python
# test_components.py
from custom_components.property_carousel import PropertyCarouselComponent

def test_property_carousel_rules():
    component = PropertyCarouselComponent()

    # Test with matching data
    response_with_results = {"query_results": [{"title": "House"}]}
    assert component.check_rules(response_with_results) == True

    # Test with no results
    response_empty = {"query_results": []}
    assert component.check_rules(response_empty) == False

def test_property_carousel_rendering():
    component = PropertyCarouselComponent()

    response = {
        "query_results": [{
            "code": "00001",
            "title": "Test House",
            "price": 100000,
            "defaultImagePath": "https://...",
            "propertyArea": 100,
            "numberOfRooms": 3
        }]
    }

    widget = component.render(response)
    assert widget is not None
    assert widget.type == "Card"
```

## Files

- `base.py` - CustomComponent abstract base class
- `__init__.py` - ComponentRegistry implementation
- `property_carousel.py` - Property search results carousel
- `property_detail.py` - Property detail view card
- `README.md` - This documentation

## See Also

- `../examples/custom_widgets.py` - Low-level widget builders
- `../examples/DRILLDOWN_USAGE.md` - Drilldown carousel usage guide
- `../DOCUMENTATION.md` - Complete project documentation
