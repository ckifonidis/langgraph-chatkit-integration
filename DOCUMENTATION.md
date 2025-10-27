# LangGraph ChatKit Integration - Complete Documentation

> Comprehensive guide for integrating ChatKit with LangGraph API backend

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Architecture](#architecture)
4. [ChatKit Protocol](#chatkit-protocol)
5. [Widgets System](#widgets-system)
6. [Advanced Features](#advanced-features)
7. [Implementation Guide](#implementation-guide)
8. [Best Practices](#best-practices)
9. [API Reference](#api-reference)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### What This Is

This project demonstrates how to integrate ChatKit with a LangGraph API backend, replacing the OpenAI Agents SDK with your custom LangGraph deployment. It provides:

- **FastAPI backend** that streams responses from a LangGraph API
- **ChatKit React UI** with conversation management
- **Thread persistence** using backend MemoryStore
- **Streaming support** for real-time AI responses
- **Rich interactive widgets** for enhanced UX
- **Greek language support** and multilingual conversations
- **Per-user thread isolation** with session management

### Key Features

- ✅ Session-based user identification
- ✅ Per-user thread filtering and isolation
- ✅ Real-time streaming responses via SSE
- ✅ Custom interactive widgets (carousels, buttons, forms)
- ✅ Message feedback and retry support
- ✅ Client-side and server-side action handling
- ✅ Theme-aware UI components (light/dark mode)

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18.18+, npm 9+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or `pip`
- Access to a LangGraph API endpoint

### Environment Variables

Create a `.env` file with:

```bash
# LangGraph API Configuration
LANGGRAPH_API_URL="https://your-langgraph-api.com"
LANGGRAPH_ASSISTANT_ID="agent"  # defaults to "agent"

# Session Security (generate with: python -c "import secrets; print(secrets.token_hex(32))")
SESSION_SECRET_KEY="your-secret-key-here"
```

### Quick Start

From the project root directory:

```bash
# Export environment variables
export LANGGRAPH_API_URL="https://your-langgraph-api.com"

# Start both backend and frontend
npm start
```

This starts:
- **Backend**: http://localhost:8004
- **Frontend**: http://localhost:5174

### Testing the Installation

1. **Health check:**
   ```bash
   curl http://localhost:8004/langgraph/health
   ```

2. **Try these prompts:**
   - "Hello, what can you help me with?"
   - "Πες μου για τα δάνεια μου" (Greek)
   - "show me a carousel"
   - "Tell me about banking services"

---

## Architecture

### System Overview

```
User Message → ChatKit UI → FastAPI Backend → LangGraph API
                    ↑                              ↓
                    └──────── Streaming Response ──┘
```

### Component Structure

#### Backend (`backend/app/`)

| Component | Purpose |
|-----------|---------|
| `main.py` | FastAPI app with `/langgraph/chatkit` endpoint |
| `langgraph_chatkit_server.py` | Adapter that converts LangGraph events to ChatKit format |
| `langgraph_client.py` | Client for streaming from LangGraph API |
| `memory_store.py` | Thread and message persistence with per-user filtering |
| `custom_widgets.py` | Reusable widget factory functions |

#### Frontend (`frontend/src/`)

- Standard ChatKit React components
- Configured to use `/langgraph/chatkit` endpoint
- Custom starter prompts for domain-specific use cases
- Widget action handlers

### Data Flow

1. **User sends message** through ChatKit UI
2. **Backend receives** message via POST to `/langgraph/chatkit`
3. **LangGraph API** is called with streaming enabled
4. **Events are buffered** until final AI response
5. **Response is converted** to ChatKit format
6. **Stream is sent** back to UI in real-time via SSE

---

## ChatKit Protocol

### Primary API Endpoint

All ChatKit communication goes through a single endpoint:

```
POST /langgraph/chatkit
Content-Type: application/json
```

This endpoint handles all protocol message types.

### Message Types

#### 1. `threads.list` - Get Thread History

**Request:**
```json
{
  "type": "threads.list",
  "params": {
    "limit": 9999,
    "order": "desc"
  }
}
```

**Response:**
```json
{
  "data": [
    {
      "id": "thr_d962848b",
      "created_at": "2025-10-24T12:28:32.205816",
      "status": { "type": "active" },
      "metadata": { "title": "My conversation" },
      "items": {
        "data": [],
        "has_more": false
      }
    }
  ],
  "has_more": false
}
```

**Key Implementation:** Threads are filtered by user session ID on the backend.

#### 2. `threads.create` - Create New Thread

**Expected Behavior:**
- Creates thread with unique ID (format: `thr_<8char_hex>`)
- Associates thread with current user session
- Returns thread metadata

#### 3. `messages.create` - Send Message

**Request:**
```json
{
  "type": "messages.create",
  "thread_id": "thr_abc123",
  "message": {
    "content": [{ "text": "Hello" }]
  }
}
```

**Response:** Server-Sent Events (SSE)
```
event: thread.item.delta
data: {"delta": ...}

event: thread.item.done
data: {"item": ...}
```

### Thread Structure

```typescript
interface Thread {
  id: string;              // Format: "thr_<8char_hex>"
  created_at: string;      // ISO 8601 timestamp
  status: {
    type: "active" | "archived";
  };
  metadata: Record<string, any>;
  items?: {
    data: ThreadItem[];
    has_more: boolean;
  };
}
```

### Thread Item Structure

```typescript
interface ThreadItem {
  id: string;              // Format: "msg_<8char_hex>"
  thread_id: string;
  created_at: string;
  content: Array<{
    text?: string;
    // ... other content types
  }>;
  status: "completed" | "in_progress" | "failed";
  metadata?: Record<string, any>;
}
```

### Session Management

**User Identification:**
```python
# In main.py - chatkit_endpoint
if "user_id" not in request.session:
    import uuid
    request.session["user_id"] = str(uuid.uuid4())

user_id = request.session["user_id"]
```

**Session Configuration:**
```python
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    session_cookie="chatkit_session",
    max_age=86400 * 30,  # 30 days
    same_site="lax",
    https_only=False,  # Set to True in production
)
```

**Per-User Thread Filtering:**
```python
# In MemoryStore.load_threads()
user_id = context.get("user_id", "anonymous")
user_thread_ids = self._user_threads.get(user_id, set())
threads = [t for t in all_threads if t.id in user_thread_ids]
```

---

## Widgets System

### What Are Widgets?

Widgets are **interactive UI components** sent from the backend and rendered in the ChatKit interface. They enable rich, interactive experiences beyond simple text messages.

### Widget Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Backend   │ ──────> │ ChatKit API  │ ──────> │  Frontend   │
│  (Python)   │ Widget  │   Protocol   │  JSON   │ (TypeScript)│
└─────────────┘         └──────────────┘         └─────────────┘
       │                                                 │
       │ Define widget structure                        │
       │ (Card, Button, Text, etc.)                     │
       └─────────────────────────────────────────────────┘
                    Widget Action Response
```

### Available Widget Components

ChatKit provides **25 built-in widget types** that can be composed in unlimited ways:

#### Container Widgets (7 types)
1. **Card** - Primary container with actions
2. **ListView** - List of items
3. **ListViewItem** - Single list item
4. **Box** - Generic flex container
5. **Row** - Horizontal layout
6. **Col** - Vertical layout
7. **Form** - Form container

#### Interactive Widgets (7 types)
8. **Button** - Clickable button
9. **Input** - Text input field
10. **Textarea** - Multi-line text input
11. **Select** - Dropdown selector
12. **RadioGroup** - Radio button group
13. **Checkbox** - Checkbox input
14. **DatePicker** - Date selection

#### Display Widgets (10 types)
15. **Text** - Plain text
16. **Title** - Heading text
17. **Caption** - Supporting text
18. **Markdown** - Markdown content
19. **Image** - Image display
20. **Icon** - Icon display
21. **Badge** - Status badge
22. **Label** - Form label
23. **Spacer** - Flexible spacing
24. **Divider** - Visual separator

#### Special (1 type)
25. **Transition** - Animation wrapper

### Creating Custom Widgets

You create custom widgets by **composing** the built-in components. Think of it like building with LEGO blocks!

#### Example 1: Yes/No Buttons

```python
from chatkit.widgets import Card, Text, Row, Button
from chatkit.actions import ActionConfig

widget = Card(
    size="md",
    padding="md",
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
                    onClickAction=ActionConfig(
                        type="user_confirms_action",
                        payload={"choice": "no"}
                    )
                )
            ]
        )
    ]
)
```

#### Example 2: Image Carousel

```python
from backend.app.custom_widgets import create_image_carousel

carousel = create_image_carousel(
    title="Featured Products",
    items=[
        {
            "id": "prod_1",
            "image_url": "https://example.com/product1.jpg",
            "title": "Wireless Headphones",
            "description": "Premium sound quality",
            "link_url": "https://example.com/products/headphones",
            "link_label": "View Product"
        },
        {
            "id": "prod_2",
            "image_url": "https://example.com/product2.jpg",
            "title": "Smart Watch",
            "description": "Track your fitness",
            "link_url": "https://example.com/products/watch",
            "link_label": "View Product"
        }
    ]
)
```

### Widget Flow

1. **Backend creates widget** using Python classes
2. **Widget is serialized** to JSON
3. **Frontend receives** widget definition via SSE
4. **ChatKit renders** widget automatically
5. **User interacts** (clicks button, fills form)
6. **Action is sent** back to backend
7. **Backend handles** action and responds

### Streaming Widgets

```python
# Stream widget to frontend
from chatkit.types import WidgetItem
from chatkit.server import ThreadItemDoneEvent
from datetime import datetime

widget_item = WidgetItem(
    id=_gen_id("widget"),
    thread_id=thread.id,
    created_at=datetime.now(),
    widget=carousel,
    status="completed"
)

yield ThreadItemDoneEvent(item=widget_item)
```

### Widget Action Handling

#### Server-Side Actions (Default)

**Backend:**
```python
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
            # Process confirmation
            result = await perform_action()
            yield ThreadItemDoneEvent(
                item=AssistantMessageItem(
                    id=_gen_id("msg"),
                    thread_id=thread.id,
                    created_at=datetime.now(),
                    content=[AssistantMessageContent(
                        text=f"Action completed: {result}"
                    )],
                    status="completed"
                )
            )
```

#### Client-Side Actions

**Backend:**
```python
Button(
    label="Close",
    onClickAction=ActionConfig(
        type="close_modal",
        handler="client"  # Handle in frontend only
    )
)
```

**Frontend:**
```typescript
widgets: {
  async onAction(action, item) {
    if (action.type === "close_modal") {
      closeModal();
      return { success: true };
    }
  }
}
```

---

## Advanced Features

### Message Feedback

Enable users to provide thumbs up/down feedback on messages.

#### Enable in Frontend

```typescript
// frontend/src/components/ChatKitPanel.tsx
threadItemActions: {
  feedback: true,  // Enable feedback buttons
  retry: true      // Enable retry/regenerate
}
```

#### Backend Storage

Feedback is automatically stored in thread item metadata:

```python
{
  "id": "msg_abc123",
  "metadata": {
    "feedback": "positive",  # or "negative"
    "feedback_timestamp": "2025-10-25T12:05:00",
    "user_id": "user_123"
  }
}
```

#### Console Events

```javascript
// Thumbs Up
ChatKit log: message.action {action: feedback.positive}

// Thumbs Down
ChatKit log: message.action {action: feedback.negative}
```

### Message Retry/Regenerate

Allow users to regenerate assistant responses.

#### Backend Implementation

```python
async def retry_message(
    thread_id: str,
    item_id: str,
    context: dict[str, Any]
) -> AsyncIterator[ThreadStreamEvent]:
    """Regenerate an assistant message."""

    # Load the assistant message to retry
    assistant_item = await self.store.load_item(thread_id, item_id, context)

    # Find the user message that came before it
    all_items = await self.store.load_thread_items(thread_id, None, 9999, "asc", context)
    user_message_item = None

    for i, item in enumerate(all_items.data):
        if item.id == item_id and i > 0:
            user_message_item = all_items.data[i - 1]
            break

    # Delete the old assistant response
    await self.store.delete_thread_item(thread_id, item_id, context)

    # Generate new response
    async for event in self.respond(
        thread=ThreadMetadata(id=thread_id),
        item=user_message_item,
        context=context
    ):
        yield event
```

### Client-Side Tools

ChatKit supports contextual tools that modify composer behavior.

#### Tool Configuration

```typescript
tools: [
  {
    id: "search_docs",
    label: "Search docs",
    shortLabel: "Docs",
    placeholderOverride: "Search documentation",
    icon: "book-open",
    pinned: false
  }
]
```

#### Tool Handling

```typescript
onClientTool: async (invocation) => {
  if (invocation.name === "search_docs") {
    // Handle search logic
    return { success: true, result: ... };
  }
}
```

---

## Implementation Guide

### Backend Implementation

#### Step 1: Create Widget Library

Create `backend/app/custom_widgets.py`:

```python
from chatkit.widgets import Card, Button, Row, Text, Image, Col, Caption
from chatkit.actions import ActionConfig
from typing import List, Dict, Any

def create_yes_no_buttons(
    question: str,
    action_type: str,
    payload: dict = None
) -> Card:
    """Create reusable yes/no confirmation widget."""
    return Card(
        size="md",
        padding="md",
        children=[
            Text(value=question, size="md", weight="medium"),
            Row(
                gap="md",
                justify="center",
                children=[
                    Button(
                        label="Yes",
                        color="success",
                        iconStart="check-circle",
                        onClickAction=ActionConfig(
                            type=action_type,
                            payload={**(payload or {}), "answer": "yes"}
                        )
                    ),
                    Button(
                        label="No",
                        color="danger",
                        iconStart="empty-circle",
                        onClickAction=ActionConfig(
                            type=action_type,
                            payload={**(payload or {}), "answer": "no"}
                        )
                    )
                ]
            )
        ]
    )

def create_image_carousel(
    items: List[Dict[str, Any]],
    title: str = None,
) -> Card:
    """Create horizontal scrollable image carousel."""
    carousel_items = []

    for item in items:
        carousel_item = Col(
            gap="sm",
            minWidth=220,
            maxWidth=220,
            children=[
                Image(
                    src=item["image_url"],
                    alt=item["title"],
                    height=180,
                    fit="cover",
                    radius="md"
                ),
                Text(value=item["title"], weight="semibold", size="md"),
                *(
                    [Caption(value=item["description"], color="secondary")]
                    if item.get("description")
                    else []
                ),
                *(
                    [Button(
                        label=item.get("link_label", "View"),
                        size="sm",
                        block=True,
                        onClickAction=ActionConfig(
                            type="open_link",
                            payload={"link_url": item.get("link_url")},
                            handler="client"
                        )
                    )]
                    if item.get("link_url")
                    else []
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

#### Step 2: Use Widgets in Response

In `backend/app/langgraph_chatkit_server.py`:

```python
from .custom_widgets import create_image_carousel, create_yes_no_buttons
from chatkit.types import WidgetItem
from chatkit.server import ThreadItemDoneEvent
from datetime import datetime

async def respond(
    self,
    thread: ThreadMetadata,
    item: UserMessageItem | None,
    context: dict[str, Any],
) -> AsyncIterator[ThreadStreamEvent]:

    user_message = _user_message_text(item)

    # Check for carousel trigger
    if "carousel" in user_message.lower():
        # Show text response first
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
                    "id": "item_1",
                    "image_url": "https://picsum.photos/400/300?random=1",
                    "title": "Item 1",
                    "description": "Description 1",
                    "link_url": "https://example.com/1",
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

    # ... rest of normal LangGraph response logic
```

#### Step 3: Handle Widget Actions

```python
async def action(
    self,
    thread: ThreadMetadata,
    action: Action[str, Any],
    sender: WidgetItem | None,
    context: dict[str, Any],
) -> AsyncIterator[ThreadStreamEvent]:

    if action.type == "user_decision":
        decision = action.payload.get("decision")

        response_text = (
            "Great! Proceeding with the action."
            if decision == "yes"
            else "No problem! Action cancelled."
        )

        yield ThreadItemDoneEvent(
            item=AssistantMessageItem(
                id=_gen_id("msg"),
                thread_id=thread.id,
                created_at=datetime.now(),
                content=[AssistantMessageContent(text=response_text)],
                status="completed"
            )
        )
```

### Frontend Implementation

#### Step 1: Configure Widget Handler

In `frontend/src/components/ChatKitPanel.tsx`:

```typescript
import { ChatKit, useChatKit } from "@openai/chatkit-react";

export function ChatKitPanel({ ... }: ChatKitPanelProps) {
  const chatkit = useChatKit({
    api: {
      url: CHATKIT_API_URL,
      domainKey: CHATKIT_API_DOMAIN_KEY
    },

    // Widget action handler
    widgets: {
      async onAction(action, item) {
        console.log("Widget action:", action);

        // Handle carousel item clicks
        if (action.type === "open_link") {
          const linkUrl = action.payload?.link_url;
          if (linkUrl) {
            window.open(linkUrl, "_blank", "noopener,noreferrer");
            return;
          }
        }

        // Other client-side actions
        if (action.type === "close_modal") {
          // Handle locally
          return { success: true };
        }

        // Server-side actions are automatically sent to backend
      }
    },

    // Enable feedback and retry
    threadItemActions: {
      feedback: true,
      retry: true
    },

    // ... rest of configuration
  });

  return <ChatKit control={chatkit.control} className="block h-full w-full" />;
}
```

---

## Best Practices

### Widget Design

1. **Create Factory Functions** - Build reusable widget generators
   ```python
   def create_confirmation(question, action_type):
       return Card(children=[...])
   ```

2. **Use Type Hints** - Enable better IDE support
   ```python
   from chatkit.widgets import Card

   def create_widget(...) -> Card:
       return Card(children=[...])
   ```

3. **Separate Concerns** - Organize widgets by type
   ```python
   # widgets/dialogs.py
   def confirmation_dialog(...): ...

   # widgets/forms.py
   def survey_form(...): ...
   ```

4. **Make Widgets Configurable** - Accept parameters for flexibility
   ```python
   def create_button_row(buttons, gap="md", justify="center"):
       return Row(gap=gap, justify=justify, children=[...])
   ```

### Action Handling

1. **Descriptive Action Types**
   ```python
   # Good ✓
   ActionConfig(type="confirm_deletion", payload={"item_id": "123"})

   # Bad ✗
   ActionConfig(type="action1", payload={"data": "stuff"})
   ```

2. **Provide Payload Context**
   ```python
   payload={
       "item_id": item.id,
       "item_type": "document",
       "confirmation_required": True
   }
   ```

3. **Use Appropriate Loading Behaviors**
   ```python
   # For quick actions
   loadingBehavior="self"

   # For long operations
   loadingBehavior="container"
   ```

### Security

1. **Strong Session Secrets** - Generate cryptographically secure keys
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Enable HTTPS in Production**
   ```python
   SessionMiddleware(
       secret_key=SESSION_SECRET_KEY,
       https_only=True  # Set to True in production
   )
   ```

3. **Validate User Inputs** - Always validate and sanitize
4. **Rate Limiting** - Implement rate limiting on API endpoint
5. **Thread Isolation** - Ensure users can only access their own threads

### Performance

1. **Database Backend** - Use PostgreSQL/Redis instead of MemoryStore for production
2. **Caching** - Implement caching for thread lists
3. **Optimize SSE Streaming** - Buffer and batch events appropriately
4. **Pagination** - Implement proper pagination for large thread lists

---

## API Reference

### Widget Components

#### Button

```python
Button(
    label: str,                      # Button text
    iconStart: str | None,           # Icon before text
    iconEnd: str | None,             # Icon after text
    color: str,                      # primary|secondary|success|danger|warning|info
    style: str,                      # primary|secondary
    variant: str,                    # solid|soft|outline|ghost
    size: str,                       # 3xs to 3xl
    pill: bool,                      # Rounded edges
    block: bool,                     # Full width
    disabled: bool,                  # Disabled state
    submit: bool,                    # Acts as form submit
    onClickAction: ActionConfig,     # Click handler
)
```

#### Card

```python
Card(
    size: str,                       # sm|md|lg|full
    padding: str,                    # spacing value
    background: str | dict,          # color or ThemeColor
    border: int | dict,              # border configuration
    radius: str,                     # border radius
    children: List[Widget],          # child widgets
    confirm: CardAction | None,      # confirm action
    cancel: CardAction | None,       # cancel action
    collapsed: bool,                 # start collapsed
    status: dict | None,             # status header
)
```

#### Row / Col

```python
Row(
    gap: str,                        # spacing between items
    justify: str,                    # start|center|end|between|around|evenly
    align: str,                      # start|center|end|baseline|stretch
    wrap: str,                       # wrap|nowrap
    children: List[Widget],          # child widgets
)

Col(
    gap: str,                        # spacing between items
    align: str,                      # start|center|end|stretch
    children: List[Widget],          # child widgets
)
```

### Custom Widget Functions

#### create_image_carousel()

```python
def create_image_carousel(
    items: List[Dict[str, Any]],
    title: str = None,
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
- `title` (str, optional): Carousel heading

**Returns:** `Card` widget

#### create_yes_no_buttons()

```python
def create_yes_no_buttons(
    question: str,
    action_type: str,
    payload: dict = None
) -> Card
```

**Parameters:**
- `question` (str): Question to display
- `action_type` (str): Action type identifier
- `payload` (dict, optional): Additional payload data

**Returns:** `Card` widget with yes/no buttons

### Available Icons

Common icons you can use in widgets:

```python
# Actions
"check", "check-circle", "check-circle-filled"
"empty-circle", "dot", "plus", "close"
"write", "reload", "search", "play"

# Navigation
"chevron-left", "chevron-right", "external-link"

# Objects
"book-open", "calendar", "mail", "phone"
"document", "cube", "suitcase"

# Status
"info", "circle-question", "bolt", "bug"
"lightbulb", "sparkle", "star", "star-filled"

# Tools
"settings-slider", "keys", "square-code"
"chart", "analytics"

# Profile
"user", "profile", "name"
```

---

## Troubleshooting

### Images Not Loading in Carousel

**Problem:** Images don't display in carousel widget

**Solutions:**
1. Check image URLs are publicly accessible
2. Verify CORS headers allow the images
3. Use HTTPS URLs (not HTTP)
4. Check browser console for errors

### Links Not Opening

**Problem:** Clicking carousel items doesn't open links

**Solutions:**
1. Verify `link_url` is in the payload
2. Check `widgets.onAction` handler is configured
3. Check browser pop-up blocker settings
4. Look for errors in browser console

### Thread Isolation Issues

**Problem:** Users see threads from other users

**Solutions:**
1. Verify session middleware is configured
2. Check session cookie is being set
3. Ensure `user_id` is in session context
4. Verify `load_threads()` filters by `user_id`

**Test with:**
```bash
# Open in different browsers
# Chrome: http://localhost:5174
# Firefox: http://localhost:5174
# Create threads in each and verify isolation
```

### Widget Not Rendering

**Problem:** Widget doesn't appear in chat

**Solutions:**
1. Check widget is yielded via `ThreadItemDoneEvent`
2. Verify widget structure is valid
3. Check browser console for validation errors
4. Ensure all required widget properties are provided

### Streaming Issues

**Problem:** Responses don't stream properly

**Solutions:**
1. Check SSE headers are correct
2. Verify `Content-Type: text/event-stream`
3. Check backend is yielding events properly
4. Test with curl to isolate frontend/backend issue

---

## Production Deployment

### Security Checklist

- [ ] Generate strong `SESSION_SECRET_KEY`
- [ ] Enable `https_only=True` for session cookies
- [ ] Implement rate limiting on API endpoint
- [ ] Validate all user inputs
- [ ] Use environment variables for secrets
- [ ] Enable CORS only for trusted domains

### Performance Optimization

- [ ] Replace MemoryStore with PostgreSQL/Redis
- [ ] Implement caching for thread lists
- [ ] Add database indexes for queries
- [ ] Optimize SSE streaming buffer size
- [ ] Enable response compression
- [ ] Add health checks and monitoring

### Scalability

- [ ] Move to persistent storage backend
- [ ] Implement horizontal scaling with shared session store
- [ ] Add load balancer
- [ ] Set up distributed caching (Redis)
- [ ] Monitor memory and CPU usage
- [ ] Plan for database scaling

---

## Additional Resources

- [ChatKit Documentation](https://docs.chatkit.studio)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Server-Sent Events Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)

---

## Summary

This documentation covers the complete LangGraph ChatKit integration, including:

✅ **Project setup and architecture**
✅ **ChatKit protocol implementation**
✅ **Widget system with custom components**
✅ **Advanced features (feedback, retry, tools)**
✅ **Complete implementation guide**
✅ **Best practices and troubleshooting**

The integration provides a production-ready foundation for building conversational AI applications with rich interactive UIs and seamless LangGraph backend integration.
