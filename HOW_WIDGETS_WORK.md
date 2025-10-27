# How ChatKit Widgets Work - Complete Guide

## Overview

Widgets are **interactive UI components** that are sent from the backend and rendered in the ChatKit interface. They allow you to create rich, interactive experiences beyond simple text messages.

## Widget Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Backend   │ ──────> │ ChatKit API  │ ──────> │  Frontend   │
│  (Python)   │ Widget  │   Protocol   │  JSON   │ (TypeScript)│
│             │  Data   │              │         │             │
└─────────────┘         └──────────────┘         └─────────────┘
       │                                                 │
       │ Define widget structure                        │
       │ (Card, Button, Text, etc.)                     │
       │                                                 │
       └─────────────────────────────────────────────────┘
                    Widget Action Response
```

## How Widgets Flow

### 1. Backend Creates Widget

```python
from chatkit.widgets import Card, Text, Row, Button
from chatkit.actions import ActionConfig

# In your backend response method
widget = Card(
    children=[
        Text(
            value="Would you like to proceed?",
            size="md",
            weight="semibold"
        ),
        Row(
            gap="md",
            justify="center",
            children=[
                Button(
                    label="Yes",
                    iconStart="check-circle",
                    color="success",
                    style="primary",
                    size="md",
                    onClickAction=ActionConfig(
                        type="user_confirms_action",
                        payload={"choice": "yes"}
                    )
                ),
                Button(
                    label="No",
                    iconStart="empty-circle",
                    color="danger",
                    style="secondary",
                    size="md",
                    onClickAction=ActionConfig(
                        type="user_confirms_action",
                        payload={"choice": "no"}
                    )
                )
            ]
        )
    ]
)

# Stream the widget to the frontend
await ctx.context.stream_widget(widget)
```

### 2. Widget is Sent via ChatKit Protocol

The widget is serialized to JSON and sent as part of a `ThreadStreamEvent`:

```json
{
  "type": "thread.item.done",
  "item": {
    "type": "widget",
    "widget": {
      "type": "Card",
      "children": [
        {
          "type": "Text",
          "value": "Would you like to proceed?",
          "size": "md",
          "weight": "semibold"
        },
        {
          "type": "Row",
          "gap": "md",
          "justify": "center",
          "children": [
            {
              "type": "Button",
              "label": "Yes",
              "iconStart": "check-circle",
              "color": "success",
              "style": "primary",
              "size": "md",
              "onClickAction": {
                "type": "user_confirms_action",
                "payload": {"choice": "yes"}
              }
            },
            {
              "type": "Button",
              "label": "No",
              "iconStart": "empty-circle",
              "color": "danger",
              "style": "secondary",
              "size": "md",
              "onClickAction": {
                "type": "user_confirms_action",
                "payload": {"choice": "no"}
              }
            }
          ]
        }
      ]
    }
  }
}
```

### 3. Frontend Renders Widget

ChatKit automatically renders the widget based on the JSON structure. The user sees:

```
┌────────────────────────────────┐
│  Would you like to proceed?    │
│                                 │
│   [✓ Yes]   [ ○ No]            │
└────────────────────────────────┘
```

### 4. User Clicks Button

When the user clicks "Yes" or "No":

**Console Log:**
```javascript
ChatKit log: widget.action {
  widgetType: "Button",
  actionType: "user_confirms_action",
  payload: {"choice": "yes"}
}
```

**Action is Sent to Backend:**
```
POST /chatkit
{
  "type": "action",
  "thread_id": "thr_abc123",
  "action": {
    "type": "user_confirms_action",
    "payload": {"choice": "yes"}
  },
  "sender": {
    "id": "widget_xyz",
    "type": "widget"
  }
}
```

### 5. Backend Handles Action

```python
# In your ChatKitServer class
async def action(
    self,
    thread: ThreadMetadata,
    action: Action[str, Any],
    sender: WidgetItem | None,
    context: dict,
) -> AsyncIterator[ThreadStreamEvent]:

    if action.type == "user_confirms_action":
        choice = action.payload.get("choice")

        if choice == "yes":
            # User confirmed - proceed with action
            result = await perform_confirmed_action()

            # Send response back
            yield ThreadItemDoneEvent(
                item=AssistantMessageItem(
                    id=generate_id(),
                    thread_id=thread.id,
                    created_at=datetime.now(),
                    content=[AssistantMessageContent(
                        text=f"Great! Proceeding with the action: {result}"
                    )],
                    status="completed"
                )
            )
        else:
            # User declined
            yield ThreadItemDoneEvent(
                item=AssistantMessageItem(
                    id=generate_id(),
                    thread_id=thread.id,
                    created_at=datetime.now(),
                    content=[AssistantMessageContent(
                        text="No problem! Action cancelled."
                    )],
                    status="completed"
                )
            )
```

## Widget Component Types

### Container Widgets

#### 1. Card
Primary container for widgets.

```python
Card(
    size="md",              # sm | md | lg | full
    padding="md",           # spacing value
    background="#f0f0f0",   # color or ThemeColor
    theme="light",          # light | dark
    children=[...]          # list of widgets
)
```

**Special Card Actions:**
```python
Card(
    confirm=CardAction(
        label="Save",
        action=ActionConfig(type="save_form", payload={})
    ),
    cancel=CardAction(
        label="Cancel",
        action=ActionConfig(type="cancel_form", payload={})
    ),
    children=[...]
)
```

#### 2. ListView
Shows a list of clickable items.

```python
ListView(
    children=[
        ListViewItem(
            onClickAction=ActionConfig(type="select_item", payload={"id": 1}),
            children=[
                Icon(name="mail"),
                Text(value="Email Widget"),
                Caption(value="Craft and preview emails", color="secondary")
            ]
        ),
        ListViewItem(
            onClickAction=ActionConfig(type="select_item", payload={"id": 2}),
            children=[
                Icon(name="calendar"),
                Text(value="Calendar Widget"),
                Caption(value="Add events to your calendar", color="secondary")
            ]
        )
    ]
)
```

#### 3. Layout Containers

**Row** - Horizontal layout:
```python
Row(
    gap="md",              # spacing between items
    justify="center",      # start|center|end|between|around|evenly
    align="center",        # start|center|end|baseline|stretch
    children=[...]
)
```

**Col** - Vertical layout:
```python
Col(
    gap="sm",
    align="start",
    children=[...]
)
```

**Box** - Generic flex container:
```python
Box(
    direction="row",       # row | col
    gap="lg",
    padding="md",
    background="#ffffff",
    children=[...]
)
```

### Interactive Widgets

#### Button
The most important widget for yes/no interactions!

```python
from chatkit.widgets import Button
from chatkit.actions import ActionConfig

Button(
    label="Yes, Continue",           # Button text
    iconStart="check-circle",        # Icon before text
    iconEnd=None,                    # Icon after text
    color="success",                 # primary|secondary|success|danger|warning|info
    style="primary",                 # primary | secondary
    variant="solid",                 # solid|soft|outline|ghost
    size="md",                       # 3xs to 3xl
    pill=True,                       # Rounded edges
    block=False,                     # Full width
    disabled=False,                  # Disabled state
    submit=False,                    # Acts as form submit
    onClickAction=ActionConfig(
        type="confirm_yes",          # Action type identifier
        payload={"data": "value"},   # Any JSON-serializable data
        handler="server",            # "server" (default) or "client"
        loadingBehavior="container"  # "auto"|"self"|"container"|"none"
    )
)
```

**Loading Behaviors:**
- `"auto"` - Default, shows loading on button
- `"self"` - Shows loading only on button
- `"container"` - Fades and locks entire widget container
- `"none"` - No loading indicator

#### Form Widgets

**Input:**
```python
Input(
    name="email",
    inputType="email",
    placeholder="Enter your email",
    required=True,
    defaultValue=""
)
```

**Textarea:**
```python
Textarea(
    name="description",
    placeholder="Enter description",
    rows=4,
    autoResize=True
)
```

**Select:**
```python
Select(
    name="country",
    options=[
        {"value": "us", "label": "United States"},
        {"value": "uk", "label": "United Kingdom"}
    ],
    placeholder="Select country",
    onChangeAction=ActionConfig(type="country_changed")
)
```

**RadioGroup:**
```python
RadioGroup(
    name="preference",
    options=[
        {"value": "yes", "label": "Yes"},
        {"value": "no", "label": "No"}
    ],
    defaultValue="yes",
    direction="row"
)
```

**Checkbox:**
```python
Checkbox(
    name="agree",
    label="I agree to the terms",
    defaultChecked=False,
    required=True
)
```

### Display Widgets

**Text:**
```python
Text(
    value="Hello world",
    size="md",              # xs|sm|md|lg|xl
    weight="semibold",      # normal|medium|semibold|bold
    color="primary",        # color or ThemeColor
    streaming=True,         # For streaming text updates
    id="my-text"           # Required for streaming updates
)
```

**Title:**
```python
Title(
    value="Main Heading",
    size="2xl",            # sm to 5xl
    weight="bold"
)
```

**Caption:**
```python
Caption(
    value="Supporting text",
    size="sm",
    color="secondary"
)
```

**Markdown:**
```python
Markdown(
    value="# Heading\n\nSome **bold** text",
    streaming=False
)
```

**Image:**
```python
Image(
    src="https://example.com/image.png",
    alt="Description",
    width=200,
    height=150,
    fit="cover",           # cover|contain|fill|scale-down|none
    radius="md"
)
```

**Icon:**
```python
Icon(
    name="check-circle",   # See available icons list
    size="xl",
    color="success"
)
```

**Badge:**
```python
Badge(
    label="New",
    color="success",       # secondary|success|danger|warning|info|discovery
    variant="solid",       # solid|soft|outline
    size="sm"
)
```

## Complete Yes/No Button Example

### Backend Implementation

```python
# In backend/app/langgraph_chatkit_server.py
from chatkit.widgets import Card, Text, Row, Button
from chatkit.actions import ActionConfig
from chatkit.server import ThreadItemDoneEvent
from chatkit.types import WidgetItem, AssistantMessageItem, AssistantMessageContent
from datetime import datetime

class LangGraphChatKitServer(ChatKitServer[dict[str, Any]]):

    # ... existing code ...

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:

        # ... your normal message handling ...

        # After sending the AI response, add yes/no buttons
        yes_no_widget = Card(
            size="md",
            padding="md",
            children=[
                Text(
                    value="Would you like to perform this action?",
                    size="md",
                    weight="medium"
                ),
                Row(
                    gap="md",
                    justify="center",
                    children=[
                        Button(
                            label="Yes",
                            iconStart="check-circle",
                            color="success",
                            style="primary",
                            size="md",
                            pill=True,
                            onClickAction=ActionConfig(
                                type="user_confirmation",
                                payload={"choice": "yes", "message_id": ai_message_id},
                                loadingBehavior="container"
                            )
                        ),
                        Button(
                            label="No",
                            iconStart="empty-circle",
                            color="danger",
                            style="secondary",
                            size="md",
                            pill=True,
                            onClickAction=ActionConfig(
                                type="user_confirmation",
                                payload={"choice": "no", "message_id": ai_message_id}
                            )
                        )
                    ]
                )
            ]
        )

        # Stream the widget
        widget_id = _gen_id("widget")
        widget_item = WidgetItem(
            id=widget_id,
            thread_id=thread.id,
            created_at=datetime.now(),
            widget=yes_no_widget,
            status="completed"
        )

        yield ThreadItemDoneEvent(item=widget_item)


    # Handle button click actions
    async def action(
        self,
        thread: ThreadMetadata,
        action: Action[str, Any],
        sender: WidgetItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:

        if action.type == "user_confirmation":
            choice = action.payload.get("choice")
            message_id = action.payload.get("message_id")

            if choice == "yes":
                # User confirmed
                result_text = "Great! I'll proceed with the action."
            else:
                # User declined
                result_text = "No problem! I've cancelled the action."

            # Send response message
            response_id = _gen_id("msg")
            response_item = AssistantMessageItem(
                id=response_id,
                thread_id=thread.id,
                created_at=datetime.now(),
                content=[AssistantMessageContent(text=result_text)],
                status="completed"
            )

            yield ThreadItemDoneEvent(item=response_item)
```

### Frontend Implementation

```typescript
// In frontend/src/components/ChatKitPanel.tsx
import { ChatKit, useChatKit } from "@openai/chatkit-react";

export function ChatKitPanel({ ... }: ChatKitPanelProps) {
  const chatkit = useChatKit({
    api: { url: CHATKIT_API_URL, domainKey: CHATKIT_API_DOMAIN_KEY },

    // ... existing config ...

    // Handle widget actions
    widgets: {
      async onAction(action, item) {
        console.log("Widget action:", action);

        if (action.type === "user_confirmation") {
          // Action is automatically sent to backend
          // No additional handling needed unless you want client-side effects
          console.log("User chose:", action.payload.choice);

          // Optional: Show local feedback
          if (action.payload.choice === "yes") {
            console.log("User confirmed!");
          }
        }

        // Return value is optional
        return { success: true };
      },
    },

    // ... rest of config ...
  });

  return <ChatKit control={chatkit.control} className="block h-full w-full" />;
}
```

## Action Handling: Client vs Server

### Server-Side Actions (Default)

Actions are sent to your backend for processing:

```python
Button(
    label="Save",
    onClickAction=ActionConfig(
        type="save_data",
        payload={"id": 123},
        handler="server"  # or omit (server is default)
    )
)
```

**Flow:**
1. User clicks button
2. Action sent to `POST /chatkit`
3. Your `action()` method processes it
4. You yield response events

### Client-Side Actions

Actions are handled entirely in the frontend:

```python
Button(
    label="Close",
    onClickAction=ActionConfig(
        type="close_modal",
        handler="client"  # Handle in frontend only
    )
)
```

**Frontend handling:**
```typescript
widgets: {
  async onAction(action, item) {
    if (action.type === "close_modal") {
      // Handle entirely client-side
      closeModal();
      return { success: true };
    }
  }
}
```

## Streaming Widgets

For dynamic content that updates over time:

```python
async def streaming_widget_example(ctx: RunContextWrapper[AgentContext]):
    # Generator that yields updated widget versions
    async def widget_updates():
        for i in range(5):
            yield Card(
                children=[
                    Text(
                        id="counter",  # ID required for streaming updates
                        value=f"Count: {i}",
                        streaming=True
                    )
                ]
            )
            await asyncio.sleep(1)

    await ctx.context.stream_widget(widget_updates())
```

**Only `Text` and `Markdown` components with an `id` will stream updates!**

## Widget Best Practices

### 1. Use Appropriate Containers

```python
# For simple yes/no: Use Card + Row
Card(children=[Text(...), Row(children=[Button(...), Button(...)])])

# For lists: Use ListView
ListView(children=[ListViewItem(...), ListViewItem(...)])

# For forms: Use Form + Card
Card(asForm=True, children=[Input(...), Button(submit=True)])
```

### 2. Action Types Should Be Descriptive

```python
# Good ✓
ActionConfig(type="confirm_deletion", payload={"item_id": "123"})
ActionConfig(type="select_payment_method", payload={"method": "card"})

# Bad ✗
ActionConfig(type="action1", payload={"data": "stuff"})
ActionConfig(type="click", payload={})
```

### 3. Provide Payload Context

```python
# Include enough context for the backend to process
Button(
    label="Delete",
    onClickAction=ActionConfig(
        type="delete_item",
        payload={
            "item_id": item.id,
            "item_type": "document",
            "confirmation_required": True
        }
    )
)
```

### 4. Use Loading Behaviors Appropriately

```python
# For quick actions
Button(..., onClickAction=ActionConfig(..., loadingBehavior="self"))

# For long operations that should block UI
Button(..., onClickAction=ActionConfig(..., loadingBehavior="container"))

# For actions that navigate away
Button(..., onClickAction=ActionConfig(..., loadingBehavior="none"))
```

## Available Icons

From the type definitions, available widget icons include:

```python
# Common UI icons
"check", "check-circle", "check-circle-filled"
"empty-circle", "dot"
"plus", "close"

# Navigation
"chevron-left", "chevron-right"
"external-link"

# Actions
"write", "write-alt", "write-alt2"
"reload", "play"
"search"

# Objects
"book-open", "book-closed", "book-clock"
"document", "page-blank"
"mail", "phone"
"calendar", "map-pin", "maps"
"cube", "suitcase"

# Status
"info", "circle-question"
"bolt", "bug"
"lightbulb", "sparkle", "sparkle-double"
"star", "star-filled"
"confetti", "wreath"

# Tools
"settings-slider", "keys"
"square-code", "square-image", "square-text"
"images", "chart", "analytics"

# Profile
"user", "profile", "profile-card", "name"

# Tech
"agent", "batch", "lab", "atom"
"desktop", "mobile", "globe"
"compass", "lifesaver", "notebook", "notebook-pencil"
"dots-horizontal", "dots-vertical"
```

## Form Example with Validation

```python
Form(
    direction="col",
    onSubmitAction=ActionConfig(
        type="submit_survey",
        payload={"survey_id": "survey_123"}
    ),
    children=[
        Title(value="Quick Survey"),

        Label(value="Your Name", fieldName="name"),
        Input(
            name="name",
            required=True,
            placeholder="John Doe"
        ),

        Label(value="Email", fieldName="email"),
        Input(
            name="email",
            inputType="email",
            required=True,
            placeholder="john@example.com"
        ),

        Label(value="Feedback", fieldName="feedback"),
        Textarea(
            name="feedback",
            rows=4,
            placeholder="Tell us what you think..."
        ),

        Row(
            gap="md",
            justify="end",
            children=[
                Button(
                    label="Cancel",
                    style="secondary",
                    onClickAction=ActionConfig(
                        type="cancel_survey",
                        handler="client"
                    )
                ),
                Button(
                    label="Submit",
                    style="primary",
                    submit=True,  # This triggers the form's onSubmitAction
                    color="success"
                )
            ]
        )
    ]
)
```

**Form submission handler:**
```python
async def action(self, thread, action, sender, context):
    if action.type == "submit_survey":
        # Form data is in action.payload
        name = action.payload.get("name")
        email = action.payload.get("email")
        feedback = action.payload.get("feedback")

        # Process the data
        await save_survey_response(name, email, feedback)

        # Send confirmation
        yield ThreadItemDoneEvent(...)
```

## Quick Reference: Yes/No Buttons

### Minimal Example

**Backend:**
```python
from chatkit.widgets import Card, Row, Button
from chatkit.actions import ActionConfig

widget = Card(
    children=[
        Row(
            gap="sm",
            children=[
                Button(
                    label="Yes",
                    color="success",
                    onClickAction=ActionConfig(type="yes")
                ),
                Button(
                    label="No",
                    color="danger",
                    onClickAction=ActionConfig(type="no")
                )
            ]
        )
    ]
)
```

**Frontend:**
```typescript
widgets: {
  async onAction(action) {
    console.log('User clicked:', action.type); // "yes" or "no"
  }
}
```

## Missing Types to Import

You'll need to add these imports to your backend:

```python
from chatkit.widgets import (
    Card, Button, Row, Col, Text, Title, Caption,
    Icon, Image, Badge, Markdown, Box, Spacer,
    ListView, ListViewItem, Form, Input, Textarea,
    Select, RadioGroup, Checkbox, Label, Divider
)
from chatkit.actions import ActionConfig
from chatkit.types import WidgetItem, Action
```

## Next Steps

1. **Add widget support to your backend**
2. **Implement the `action()` method** in `LangGraphChatKitServer`
3. **Add `widgets.onAction` callback** in frontend
4. **Test with simple yes/no buttons**
5. **Expand to more complex forms/interactions**

## Summary

**Widgets work by:**
1. ✅ Backend creates widget structure (Card, Button, etc.)
2. ✅ Widget streamed via `stream_widget()` or `ThreadItemDoneEvent`
3. ✅ Frontend automatically renders the widget
4. ✅ User interacts (clicks button)
5. ✅ Action sent to backend (via `action()` method)
6. ✅ Backend processes action and responds

**For yes/no buttons specifically:**
- Use `Row` containing two `Button` widgets
- Each button has an `onClickAction` with unique `type`
- Backend's `action()` method handles the response
- Frontend's `widgets.onAction` callback is optional (for client-side effects)
