# Usage Examples

## Quick Start

### 1. Basic Server Setup

```python
from chatkit_langgraph import LangGraphChatKitServer

# Create server
server = LangGraphChatKitServer(
    langgraph_url="https://your-langgraph-api.com",
    assistant_id="your-assistant-id"
)

# Use with FastAPI
from fastapi import FastAPI
app = FastAPI()
app.post("/chatkit")(server.handle_request)
```

### 2. Using Environment Variables

```bash
# Set environment variables
export LANGGRAPH_API_URL="https://your-api.com"
export LANGGRAPH_ASSISTANT_ID="your-assistant"
export LANGGRAPH_TIMEOUT="60.0"
```

```python
from chatkit_langgraph import create_server_from_env

# Automatically reads from environment
server = create_server_from_env()
```

### 3. With Custom Message Handlers

```python
from chatkit_langgraph import create_server_from_env
from examples.carousel_handler import CarouselWidgetHandler

server = create_server_from_env(
    message_handlers=[
        CarouselWidgetHandler(
            trigger_keywords=["show products", "carousel", "browse"]
        )
    ]
)
```

## Custom Handler Example

### Creating a Help Command Handler

```python
from chatkit_langgraph import MessageHandler
from chatkit.types import (
    ThreadMetadata,
    ThreadStreamEvent,
    AssistantMessageItem,
    AssistantMessageContent
)
from chatkit.server import ThreadItemDoneEvent
from datetime import datetime
from uuid import uuid4
from typing import Any, AsyncIterator


class HelpCommandHandler(MessageHandler):
    """Handler for /help command."""

    async def should_handle(
        self,
        user_message: str,
        thread: ThreadMetadata,
        context: dict[str, Any]
    ) -> bool:
        return user_message.strip().lower() in ["/help", "help"]

    async def handle(
        self,
        user_message: str,
        thread: ThreadMetadata,
        context: dict[str, Any]
    ) -> AsyncIterator[ThreadStreamEvent]:
        help_text = """
**Available Commands:**

- `/help` - Show this help message
- `show products` - Display product carousel
- Ask any question to chat with the AI assistant

**Tips:**
- Be specific in your questions
- You can ask follow-up questions
- Use natural language
        """

        message = AssistantMessageItem(
            id=f"msg_{uuid4().hex[:8]}",
            thread_id=thread.id,
            created_at=datetime.now(),
            content=[AssistantMessageContent(text=help_text)],
            status="completed"
        )

        yield ThreadItemDoneEvent(item=message)


# Use the handler
from chatkit_langgraph import create_server_from_env

server = create_server_from_env(
    message_handlers=[HelpCommandHandler()]
)
```

### Creating a Widget Handler

```python
from chatkit_langgraph import MessageHandler
from chatkit.types import ThreadMetadata, ThreadStreamEvent, WidgetItem
from chatkit.server import ThreadItemDoneEvent
from chatkit.widgets import Card, Text, Button
from chatkit.actions import ActionConfig
from datetime import datetime
from uuid import uuid4
from typing import Any, AsyncIterator


class QuickActionsHandler(MessageHandler):
    """Shows quick action buttons."""

    async def should_handle(
        self,
        user_message: str,
        thread: ThreadMetadata,
        context: dict[str, Any]
    ) -> bool:
        return "quick actions" in user_message.lower()

    async def handle(
        self,
        user_message: str,
        thread: ThreadMetadata,
        context: dict[str, Any]
    ) -> AsyncIterator[ThreadStreamEvent]:
        # Create widget
        widget = Card(
            size="md",
            padding="md",
            children=[
                Text(value="Quick Actions", size="lg", weight="bold"),
                Button(
                    label="Get Help",
                    color="primary",
                    onClickAction=ActionConfig(type="help")
                ),
                Button(
                    label="Show Products",
                    color="success",
                    onClickAction=ActionConfig(type="show_products")
                ),
                Button(
                    label="Contact Support",
                    color="info",
                    onClickAction=ActionConfig(type="contact_support")
                )
            ]
        )

        widget_item = WidgetItem(
            id=f"widget_{uuid4().hex[:8]}",
            thread_id=thread.id,
            created_at=datetime.now(),
            widget=widget,
            status="completed"
        )

        yield ThreadItemDoneEvent(item=widget_item)
```

## Full FastAPI Integration

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from chatkit_langgraph import create_server_from_env
from examples.carousel_handler import CarouselWidgetHandler
import os
import uuid

app = FastAPI(title="My ChatKit App")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Sessions
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY", "change-me-in-production"),
    session_cookie="chatkit_session",
    max_age=86400 * 30,
)

# Create server
server = create_server_from_env(
    message_handlers=[
        CarouselWidgetHandler(),
        # Add more handlers here
    ]
)

@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    """ChatKit protocol endpoint."""
    # Session management
    if "user_id" not in request.session:
        request.session["user_id"] = str(uuid.uuid4())

    # Process request
    payload = await request.body()
    result = await server.process(
        payload,
        {"request": request, "user_id": request.session["user_id"]}
    )

    # Return result (handles both streaming and JSON)
    from chatkit.server import StreamingResult
    from fastapi.responses import StreamingResponse, Response

    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return result

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "langgraph_url": server.langgraph_url,
        "assistant_id": server.assistant_id
    }
```

## Testing

```python
import pytest
from chatkit_langgraph import LangGraphChatKitServer
from chatkit.types import ThreadMetadata

@pytest.fixture
def server():
    return LangGraphChatKitServer(
        langgraph_url="https://test-api.com",
        assistant_id="test-assistant"
    )

@pytest.mark.asyncio
async def test_server_initialization(server):
    assert server.langgraph_url == "https://test-api.com"
    assert server.assistant_id == "test-assistant"

@pytest.mark.asyncio
async def test_custom_handler():
    from chatkit_langgraph import MessageHandler

    class TestHandler(MessageHandler):
        async def should_handle(self, user_message, thread, context):
            return "test" in user_message

        async def handle(self, user_message, thread, context):
            # Return test response
            pass

    server = LangGraphChatKitServer(
        langgraph_url="https://test-api.com",
        assistant_id="test",
        message_handlers=[TestHandler()]
    )

    assert len(server.message_handlers) == 1
```

## Production Deployment

### With Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install -e .

# Copy application
COPY chatkit_langgraph/ chatkit_langgraph/
COPY app/ app/

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### With Custom Store

```python
from chatkit.store import Store
from chatkit_langgraph import LangGraphChatKitServer

class PostgreSQLStore(Store):
    """PostgreSQL implementation of ChatKit Store."""

    def __init__(self, db_url: str):
        self.db_url = db_url
        # Initialize connection pool, etc.

    # Implement all Store interface methods
    async def load_thread(self, thread_id, context):
        # Query from PostgreSQL
        pass

    # ... more methods

# Use custom store
server = LangGraphChatKitServer(
    langgraph_url="...",
    assistant_id="...",
    store=PostgreSQLStore(db_url="postgresql://...")
)
```

## Environment Variables

```bash
# Required
LANGGRAPH_API_URL=https://your-langgraph-api.com
LANGGRAPH_ASSISTANT_ID=your-assistant-id

# Optional
LANGGRAPH_TIMEOUT=60.0
SESSION_SECRET_KEY=your-secret-key-for-sessions

# For production
HTTPS_ONLY=true
```

## More Examples

See the `examples/` directory for more:
- `carousel_handler.py` - Product carousel widget
- `custom_widgets.py` - Widget composition examples
- `widget_examples.py` - Pre-built widget templates
