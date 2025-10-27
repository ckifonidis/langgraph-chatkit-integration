# Creating Custom Widgets in ChatKit

## TL;DR: Can You Create Custom Widgets?

**Short Answer**: ❌ No, you cannot create new widget *types*
**But**: ✅ YES, you can create custom widget *compositions* using the existing components!

ChatKit provides a **fixed set of ~25 widget component types** (Card, Button, Text, etc.), but you can combine them in unlimited ways to create any UI you need.

## Widget Components Available

ChatKit provides these built-in widget types:

### Containers (7 types)
1. `Card` - Primary container with actions
2. `ListView` - List of items
3. `ListViewItem` - Single list item
4. `Box` - Generic flex container
5. `Row` - Horizontal layout
6. `Col` - Vertical layout
7. `Form` - Form container

### Interactive (7 types)
8. `Button` - Clickable button
9. `Input` - Text input field
10. `Textarea` - Multi-line text input
11. `Select` - Dropdown selector
12. `RadioGroup` - Radio button group
13. `Checkbox` - Checkbox input
14. `DatePicker` - Date selection

### Display (10 types)
15. `Text` - Plain text
16. `Title` - Heading text
17. `Caption` - Supporting text
18. `Markdown` - Markdown content
19. `Image` - Image display
20. `Icon` - Icon display
21. `Badge` - Status badge
22. `Label` - Form label
23. `Spacer` - Flexible spacing
24. `Divider` - Visual separator

### Special (1 type)
25. `Transition` - Animation wrapper

## How to Create "Custom" Widgets

You create custom widgets by **composing** the built-in components. Think of it like building with LEGO blocks!

### Example 1: Custom Confirmation Dialog

```python
from chatkit.widgets import Card, Title, Text, Row, Button, Divider, Icon
from chatkit.actions import ActionConfig

def create_confirmation_dialog(
    title: str,
    message: str,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
    action_type: str = "user_confirmation",
    action_payload: dict = None
):
    """Create a reusable confirmation dialog widget."""
    return Card(
        size="md",
        padding="lg",
        background={"light": "#ffffff", "dark": "#1a1a1a"},
        children=[
            Row(
                gap="md",
                align="center",
                children=[
                    Icon(name="circle-question", size="xl", color="warning"),
                    Title(value=title, size="lg", weight="bold")
                ]
            ),
            Divider(spacing="md"),
            Text(
                value=message,
                size="md",
                color="secondary",
                textAlign="start"
            ),
            Row(
                gap="md",
                justify="end",
                children=[
                    Button(
                        label=cancel_label,
                        style="secondary",
                        variant="ghost",
                        onClickAction=ActionConfig(
                            type=f"{action_type}_cancel",
                            payload=action_payload or {},
                            handler="client"  # Handle cancellation client-side
                        )
                    ),
                    Button(
                        label=confirm_label,
                        style="primary",
                        color="danger",
                        iconEnd="check-circle",
                        onClickAction=ActionConfig(
                            type=action_type,
                            payload={**(action_payload or {}), "confirmed": True},
                            loadingBehavior="container"
                        )
                    )
                ]
            )
        ]
    )

# Usage:
widget = create_confirmation_dialog(
    title="Delete Item?",
    message="Are you sure you want to delete this item? This action cannot be undone.",
    confirm_label="Yes, Delete",
    cancel_label="Cancel",
    action_type="delete_item",
    action_payload={"item_id": "item_123"}
)
```

### Example 2: Custom Product Card

```python
def create_product_card(product: dict):
    """Create a custom product display card."""
    return Card(
        size="md",
        padding="md",
        children=[
            Image(
                src=product["image_url"],
                alt=product["name"],
                height=200,
                fit="cover",
                radius="md"
            ),
            Title(value=product["name"], size="xl", weight="bold"),
            Row(
                gap="sm",
                align="center",
                children=[
                    Badge(
                        label=product["category"],
                        color="info",
                        variant="soft",
                        pill=True
                    ),
                    Spacer(minSize="auto"),
                    Text(
                        value=f"${product['price']}",
                        size="xl",
                        weight="bold",
                        color="success"
                    )
                ]
            ),
            Divider(spacing="sm"),
            Text(
                value=product["description"],
                size="sm",
                color="secondary",
                maxLines=3
            ),
            Row(
                gap="md",
                justify="between",
                children=[
                    Button(
                        label="View Details",
                        style="secondary",
                        variant="outline",
                        iconEnd="external-link",
                        onClickAction=ActionConfig(
                            type="view_product",
                            payload={"product_id": product["id"]}
                        )
                    ),
                    Button(
                        label="Add to Cart",
                        style="primary",
                        color="success",
                        iconStart="plus",
                        onClickAction=ActionConfig(
                            type="add_to_cart",
                            payload={"product_id": product["id"]},
                            loadingBehavior="self"
                        )
                    )
                ]
            )
        ]
    )
```

### Example 3: Custom Multi-Step Form

```python
def create_survey_widget(step: int = 1):
    """Multi-step survey widget."""
    if step == 1:
        return Card(
            asForm=True,
            children=[
                Title(value="Customer Survey - Step 1/3", size="lg"),
                Caption(value="Tell us about yourself", color="secondary"),
                Divider(spacing="md"),

                Label(value="Your Name", fieldName="name"),
                Input(
                    name="name",
                    placeholder="John Doe",
                    required=True
                ),

                Label(value="Email", fieldName="email"),
                Input(
                    name="email",
                    inputType="email",
                    placeholder="john@example.com",
                    required=True
                ),

                Row(
                    gap="md",
                    justify="end",
                    children=[
                        Button(
                            label="Next →",
                            submit=True,
                            style="primary",
                            onClickAction=ActionConfig(
                                type="survey_step_1_complete"
                            )
                        )
                    ]
                )
            ]
        )
    elif step == 2:
        return Card(
            children=[
                Title(value="Customer Survey - Step 2/3", size="lg"),
                # ... step 2 fields
            ]
        )
    # ... more steps

```

### Example 4: Custom Status Dashboard

```python
def create_status_dashboard(metrics: dict):
    """Custom dashboard with multiple metrics."""
    return Card(
        size="lg",
        padding="lg",
        children=[
            Title(value="System Status", size="2xl", weight="bold"),

            # Metrics Row
            Row(
                gap="lg",
                justify="around",
                wrap="wrap",
                children=[
                    # Metric 1
                    Col(
                        gap="xs",
                        align="center",
                        children=[
                            Icon(name="check-circle-filled", size="3xl", color="success"),
                            Text(value=str(metrics["uptime"]), size="2xl", weight="bold"),
                            Caption(value="Uptime %", color="secondary")
                        ]
                    ),

                    # Metric 2
                    Col(
                        gap="xs",
                        align="center",
                        children=[
                            Icon(name="user", size="3xl", color="info"),
                            Text(value=str(metrics["users"]), size="2xl", weight="bold"),
                            Caption(value="Active Users", color="secondary")
                        ]
                    ),

                    # Metric 3
                    Col(
                        gap="xs",
                        align="center",
                        children=[
                            Icon(name="bolt", size="3xl", color="warning"),
                            Text(value=f"{metrics['latency']}ms", size="2xl", weight="bold"),
                            Caption(value="Avg Latency", color="secondary")
                        ]
                    )
                ]
            ),

            Divider(spacing="lg"),

            # Action buttons
            Row(
                gap="md",
                justify="center",
                children=[
                    Button(
                        label="Refresh",
                        iconStart="reload",
                        variant="outline",
                        onClickAction=ActionConfig(
                            type="refresh_dashboard",
                            loadingBehavior="container"
                        )
                    ),
                    Button(
                        label="View Details",
                        iconEnd="external-link",
                        style="primary",
                        onClickAction=ActionConfig(
                            type="view_dashboard_details"
                        )
                    )
                ]
            )
        ]
    )
```

### Example 5: Custom Yes/No with Context

```python
def create_yes_no_widget(
    question: str,
    context: dict,
    yes_label: str = "Yes",
    no_label: str = "No"
):
    """Reusable yes/no widget with context."""
    return Card(
        size="md",
        padding="md",
        background={"light": "#f8fafc", "dark": "#1e293b"},
        border={"size": 1, "color": {"light": "#e2e8f0", "dark": "#334155"}},
        radius="lg",
        children=[
            Row(
                gap="sm",
                align="center",
                children=[
                    Icon(name="circle-question", size="lg", color="primary"),
                    Text(
                        value=question,
                        size="md",
                        weight="medium"
                    )
                ]
            ),
            Spacer(minSize="md"),
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
                            type="user_decision",
                            payload={**context, "decision": "yes"}
                        )
                    ),
                    Button(
                        label=no_label,
                        iconStart="empty-circle",
                        color="danger",
                        style="secondary",
                        size="md",
                        pill=True,
                        onClickAction=ActionConfig(
                            type="user_decision",
                            payload={**context, "decision": "no"}
                        )
                    )
                ]
            )
        ]
    )

# Usage:
widget = create_yes_no_widget(
    question="Would you like to save your progress?",
    context={
        "session_id": "sess_123",
        "action": "save_progress",
        "timestamp": "2025-10-27T12:00:00Z"
    }
)
```

## Widget Composition Patterns

### Pattern 1: Card with Status Header

```python
Card(
    status={"text": "Processing...", "icon": "dot"},
    children=[
        # Your content
    ]
)
```

### Pattern 2: Collapsible Card

```python
Card(
    collapsed=True,  # Starts collapsed
    children=[
        Title(value="Click to expand"),
        # Hidden content
    ]
)
```

### Pattern 3: Card with Confirm/Cancel Actions

```python
from chatkit.widgets import CardAction

Card(
    confirm=CardAction(
        label="Save Changes",
        action=ActionConfig(type="save")
    ),
    cancel=CardAction(
        label="Discard",
        action=ActionConfig(type="cancel")
    ),
    children=[
        # Form fields or content
    ]
)
```

### Pattern 4: Nested Layouts

```python
Card(
    children=[
        Row(
            gap="lg",
            children=[
                Col(
                    gap="sm",
                    flex=2,  # Takes 2/3 of space
                    children=[
                        Title(value="Left Side"),
                        Text(value="Content...")
                    ]
                ),
                Col(
                    gap="sm",
                    flex=1,  # Takes 1/3 of space
                    children=[
                        Title(value="Right Side"),
                        Button(label="Action")
                    ]
                )
            ]
        )
    ]
)
```

## Creating Widget Libraries

You can create a library of reusable widget functions:

```python
# widgets/library.py
from chatkit.widgets import *
from chatkit.actions import ActionConfig
from typing import Dict, List, Any

class CustomWidgets:
    """Library of reusable custom widgets."""

    @staticmethod
    def yes_no_dialog(
        question: str,
        action_type: str,
        payload: dict = None
    ) -> Card:
        """Standard yes/no confirmation dialog."""
        return Card(
            children=[
                Text(value=question, size="md", weight="medium"),
                Row(
                    gap="md",
                    justify="center",
                    children=[
                        Button(
                            label="Yes",
                            color="success",
                            onClickAction=ActionConfig(
                                type=action_type,
                                payload={**(payload or {}), "answer": "yes"}
                            )
                        ),
                        Button(
                            label="No",
                            color="danger",
                            onClickAction=ActionConfig(
                                type=action_type,
                                payload={**(payload or {}), "answer": "no"}
                            )
                        )
                    ]
                )
            ]
        )

    @staticmethod
    def rating_widget(item_id: str) -> Card:
        """5-star rating widget."""
        return Card(
            children=[
                Text(value="How would you rate this?", size="sm"),
                Row(
                    gap="xs",
                    justify="center",
                    children=[
                        Button(
                            iconStart="star",
                            variant="ghost",
                            size="lg",
                            onClickAction=ActionConfig(
                                type="rate_item",
                                payload={"item_id": item_id, "rating": i}
                            )
                        )
                        for i in range(1, 6)
                    ]
                )
            ]
        )

    @staticmethod
    def loading_card(message: str = "Loading...") -> Card:
        """Loading indicator card."""
        return Card(
            status={"text": message, "icon": "dot"},
            children=[
                Row(
                    gap="md",
                    align="center",
                    justify="center",
                    padding="xl",
                    children=[
                        Icon(name="reload", size="2xl"),
                        Text(value=message, size="lg", color="secondary")
                    ]
                )
            ]
        )

    @staticmethod
    def error_card(error_message: str, retry_action: str = None) -> Card:
        """Error display with optional retry."""
        children = [
            Row(
                gap="sm",
                align="center",
                children=[
                    Icon(name="circle-question", size="xl", color="danger"),
                    Title(value="Error", size="lg", color="danger")
                ]
            ),
            Text(value=error_message, size="md", color="secondary")
        ]

        if retry_action:
            children.append(
                Row(
                    justify="end",
                    children=[
                        Button(
                            label="Retry",
                            iconStart="reload",
                            color="primary",
                            onClickAction=ActionConfig(type=retry_action)
                        )
                    ]
                )
            )

        return Card(
            background={"light": "#fef2f2", "dark": "#3f1f1f"},
            padding="md",
            children=children
        )

    @staticmethod
    def action_list(actions: List[Dict[str, Any]]) -> ListView:
        """List of actionable items."""
        return ListView(
            children=[
                ListViewItem(
                    onClickAction=ActionConfig(
                        type=action["type"],
                        payload=action.get("payload", {})
                    ),
                    children=[
                        Icon(name=action.get("icon", "dot"), size="lg"),
                        Col(
                            gap="2xs",
                            children=[
                                Text(value=action["label"], weight="medium"),
                                Caption(
                                    value=action.get("description", ""),
                                    color="secondary"
                                )
                            ]
                        )
                    ]
                )
                for action in actions
            ]
        )
```

## Using Your Custom Widget Library

```python
# In your ChatKit server respond() method
from widgets.library import CustomWidgets

# Simple yes/no
widget = CustomWidgets.yes_no_dialog(
    question="Do you want to continue?",
    action_type="continue_process",
    payload={"process_id": "proc_123"}
)

# Rating
widget = CustomWidgets.rating_widget(item_id="msg_abc123")

# Loading state
widget = CustomWidgets.loading_card("Generating response...")

# Error with retry
widget = CustomWidgets.error_card(
    error_message="Failed to fetch data. Please try again.",
    retry_action="retry_fetch"
)

# Action list
widget = CustomWidgets.action_list([
    {
        "icon": "mail",
        "label": "Send Email",
        "description": "Compose and send an email",
        "type": "open_email_composer"
    },
    {
        "icon": "calendar",
        "label": "Schedule Meeting",
        "description": "Add event to calendar",
        "type": "open_calendar"
    }
])

# Stream any widget
await ctx.context.stream_widget(widget)
```

## Advanced: JSON-Based Custom Widgets

You can also define widgets as JSON if you prefer:

```python
from chatkit.types import WidgetRoot

# Define widget as JSON
custom_widget_json = """
{
  "type": "Card",
  "size": "md",
  "padding": "md",
  "children": [
    {
      "type": "Text",
      "value": "Custom Question?",
      "size": "md",
      "weight": "medium"
    },
    {
      "type": "Row",
      "gap": "sm",
      "justify": "center",
      "children": [
        {
          "type": "Button",
          "label": "Yes",
          "color": "success",
          "onClickAction": {
            "type": "custom_action",
            "payload": {"answer": "yes"}
          }
        },
        {
          "type": "Button",
          "label": "No",
          "color": "danger",
          "onClickAction": {
            "type": "custom_action",
            "payload": {"answer": "no"}
          }
        }
      ]
    }
  ]
}
"""

# Parse and validate
try:
    widget = WidgetRoot.model_validate_json(custom_widget_json)
    await ctx.context.stream_widget(widget)
except ValidationError as e:
    print(f"Invalid widget JSON: {e}")
```

## Limitations

### What You CANNOT Do

❌ Create new widget component types (e.g., cannot add `type: "MyCustomWidget"`)
❌ Add custom CSS classes to widgets
❌ Inject arbitrary HTML or React components
❌ Override widget rendering behavior
❌ Create widgets with custom JavaScript logic embedded

### What You CAN Do

✅ Combine existing components in any way
✅ Create reusable widget factory functions
✅ Style widgets using built-in properties (colors, sizes, borders, etc.)
✅ Use custom icons (from the ~60 available icons)
✅ Define custom action types and payloads
✅ Handle actions client-side OR server-side
✅ Create streaming widgets with real-time updates
✅ Build complex forms, dashboards, dialogs, etc.

## Best Practices for Custom Widgets

### 1. Create Factory Functions

```python
# Good ✓
def create_confirmation(question, action_type):
    return Card(children=[...])

# Bad ✗
# Hardcoding widgets everywhere without reusability
```

### 2. Use Type Hints

```python
from chatkit.widgets import Card
from chatkit.types import WidgetRoot

def create_widget(...) -> Card | ListView | WidgetRoot:
    """Proper type hints for better IDE support."""
    return Card(children=[...])
```

### 3. Separate Concerns

```python
# widgets/dialogs.py
def confirmation_dialog(...): ...
def alert_dialog(...): ...

# widgets/forms.py
def survey_form(...): ...
def feedback_form(...): ...

# widgets/displays.py
def status_card(...): ...
def metric_card(...): ...
```

### 4. Make Widgets Configurable

```python
def create_button_row(
    buttons: List[Dict[str, Any]],
    gap: str = "md",
    justify: str = "center"
) -> Row:
    """Flexible button row generator."""
    return Row(
        gap=gap,
        justify=justify,
        children=[
            Button(
                label=btn["label"],
                color=btn.get("color", "primary"),
                style=btn.get("style", "primary"),
                onClickAction=ActionConfig(
                    type=btn["action_type"],
                    payload=btn.get("payload", {})
                )
            )
            for btn in buttons
        ]
    )
```

## Complete Example: Custom Booking Widget

```python
from chatkit.widgets import *
from chatkit.actions import ActionConfig
from datetime import datetime

def create_booking_widget(booking_data: dict) -> Card:
    """Complete booking confirmation widget with all details."""
    return Card(
        size="lg",
        padding="lg",
        border={"size": 2, "color": "success"},
        radius="xl",
        children=[
            # Header
            Row(
                gap="md",
                align="center",
                justify="between",
                padding={"bottom": "md"},
                children=[
                    Row(
                        gap="sm",
                        align="center",
                        children=[
                            Icon(name="calendar", size="xl", color="success"),
                            Title(value="Confirm Booking", size="xl")
                        ]
                    ),
                    Badge(label="Pending", color="warning", variant="soft")
                ]
            ),

            Divider(),

            # Booking Details
            Col(
                gap="md",
                padding={"y": "md"},
                children=[
                    Row(
                        justify="between",
                        children=[
                            Text(value="Service:", weight="semibold"),
                            Text(value=booking_data["service"])
                        ]
                    ),
                    Row(
                        justify="between",
                        children=[
                            Text(value="Date:", weight="semibold"),
                            Text(value=booking_data["date"])
                        ]
                    ),
                    Row(
                        justify="between",
                        children=[
                            Text(value="Time:", weight="semibold"),
                            Text(value=booking_data["time"])
                        ]
                    ),
                    Row(
                        justify="between",
                        children=[
                            Text(value="Price:", weight="semibold"),
                            Text(
                                value=f"${booking_data['price']}",
                                size="lg",
                                weight="bold",
                                color="success"
                            )
                        ]
                    )
                ]
            ),

            Divider(),

            # Notes
            Box(
                padding="md",
                background={"light": "#f1f5f9", "dark": "#1e293b"},
                radius="md",
                children=[
                    Caption(value="Special requests:", size="sm"),
                    Textarea(
                        name="notes",
                        placeholder="Add any special requests...",
                        rows=3,
                        defaultValue=booking_data.get("notes", "")
                    )
                ]
            ),

            Spacer(minSize="md"),

            # Action Buttons
            Row(
                gap="md",
                justify="between",
                children=[
                    Button(
                        label="Cancel",
                        variant="ghost",
                        color="danger",
                        onClickAction=ActionConfig(
                            type="cancel_booking",
                            payload={"booking_id": booking_data["id"]},
                            handler="client"
                        )
                    ),
                    Row(
                        gap="sm",
                        children=[
                            Button(
                                label="Modify",
                                style="secondary",
                                variant="outline",
                                iconStart="write",
                                onClickAction=ActionConfig(
                                    type="modify_booking",
                                    payload={"booking_id": booking_data["id"]}
                                )
                            ),
                            Button(
                                label="Confirm Booking",
                                style="primary",
                                color="success",
                                iconEnd="check-circle",
                                onClickAction=ActionConfig(
                                    type="confirm_booking",
                                    payload={"booking_id": booking_data["id"]},
                                    loadingBehavior="container"
                                )
                            )
                        ]
                    )
                ]
            )
        ]
    )
```

## Styling Options

You can customize appearance using:

### Colors
```python
# Direct colors
background="#f0f0f0"
color="#2D8CFF"

# Theme-aware colors (adapts to light/dark mode)
background={"light": "#ffffff", "dark": "#1a1a1a"}
color={"light": "#000000", "dark": "#ffffff"}

# Semantic colors
color="primary" | "secondary" | "success" | "danger" | "warning" | "info" | "discovery"
```

### Spacing
```python
# Single value
padding="md"
gap="lg"

# Object spacing
padding={"x": "md", "y": "lg"}  # horizontal and vertical
margin={"top": "sm", "bottom": "xl"}  # specific sides
```

### Borders
```python
# Simple
border=1

# Complex
border={"size": 2, "color": "#e0e0e0", "style": "dashed"}

# Per-side
border={"top": 2, "bottom": {"size": 1, "color": "success"}}
```

## Summary

**Can you create custom widgets?**

- ❌ **No** - You cannot add new widget *types* to ChatKit
- ✅ **YES** - You can create unlimited custom widget *compositions*
- ✅ **YES** - You can build reusable widget libraries
- ✅ **YES** - You can achieve almost any UI design by combining components

**The 25 built-in widget types are more than enough to build:**
- Confirmation dialogs
- Complex forms
- Data dashboards
- Product cards
- Rating systems
- Status displays
- Multi-step wizards
- And much more!

**Think of widgets like HTML/CSS** - you don't create new HTML elements, you combine existing ones creatively!
