# ChatKit LangGraph Adapter

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Production-ready adapter for integrating [LangGraph API](https://langchain-ai.github.io/langgraph/) with [OpenAI ChatKit](https://platform.openai.com/docs/chatkit).

## Features

✅ **Clean Integration** - Seamlessly connects LangGraph API with ChatKit protocol
✅ **Streaming Support** - Real-time streaming of LangGraph responses
✅ **Extensible** - Custom message handlers for widgets, commands, and routing
✅ **Type-Safe** - Full type hints with Pydantic models
✅ **Production-Ready** - Comprehensive error handling and logging
✅ **Zero Vendor Lock-in** - Works with any LangGraph deployment

## Installation

```bash
pip install chatkit-langgraph-adapter
```

For development:
```bash
pip install chatkit-langgraph-adapter[dev]
```

For running examples:
```bash
pip install chatkit-langgraph-adapter[examples]
```

## Quick Start

### Basic Usage

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

### With Environment Variables

```python
from chatkit_langgraph import create_server_from_env

# Reads from LANGGRAPH_API_URL and LANGGRAPH_ASSISTANT_ID
server = create_server_from_env()
```

### With Custom Message Handlers

```python
from chatkit_langgraph import LangGraphChatKitServer, MessageHandler
from chatkit.types import ThreadMetadata, ThreadStreamEvent
from typing import Any, AsyncIterator

class MyCustomHandler(MessageHandler):
    async def should_handle(
        self,
        user_message: str,
        thread: ThreadMetadata,
        context: dict[str, Any]
    ) -> bool:
        # Check if this handler should process the message
        return "help" in user_message.lower()

    async def handle(
        self,
        user_message: str,
        thread: ThreadMetadata,
        context: dict[str, Any]
    ) -> AsyncIterator[ThreadStreamEvent]:
        # Handle the message and yield events
        from chatkit.server import ThreadItemDoneEvent
        from chatkit.types import AssistantMessageItem, AssistantMessageContent
        from datetime import datetime

        message = AssistantMessageItem(
            id=f"msg_{uuid4().hex[:8]}",
            thread_id=thread.id,
            created_at=datetime.now(),
            content=[AssistantMessageContent(text="Here's how I can help...")],
            status="completed"
        )
        yield ThreadItemDoneEvent(item=message)

# Use custom handler
server = LangGraphChatKitServer(
    langgraph_url="https://your-langgraph-api.com",
    assistant_id="your-assistant-id",
    message_handlers=[MyCustomHandler()]
)
```

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   ChatKit UI    │◄────────│  ChatKit Server  │◄────────│  LangGraph API  │
│   (Frontend)    │  SSE    │   (Adapter)      │  HTTP   │   (Backend)     │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                     │
                                     │
                            ┌────────▼────────┐
                            │ Message Handler │
                            │   (Optional)    │
                            └─────────────────┘
```

### Components

#### `LangGraphStreamClient`
- Handles LangGraph API communication
- Parses Server-Sent Events (SSE)
- Extracts AI messages from state events
- Manages thread lifecycle

#### `LangGraphChatKitServer`
- Implements ChatKit server protocol
- Routes messages to handlers or LangGraph
- Converts LangGraph events to ChatKit format
- Manages conversation state

#### `MemoryStore`
- In-memory implementation of ChatKit Store interface
- Per-user thread isolation
- Perfect for demos and development
- Replace with persistent store for production

#### `MessageHandler` (Abstract)
- Extension point for custom logic
- Intercepts messages before LangGraph
- Use for widgets, commands, routing, etc.

## Examples

### Example 1: Widget Handler

See `examples/carousel_handler.py`:

```python
from chatkit_langgraph import LangGraphChatKitServer
from examples.carousel_handler import CarouselWidgetHandler

server = LangGraphChatKitServer(
    langgraph_url="https://your-api.com",
    assistant_id="your-assistant",
    message_handlers=[
        CarouselWidgetHandler(trigger_keywords=["show products", "carousel"])
    ]
)
```

### Example 2: Complete FastAPI App

```python
from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from chatkit_langgraph import create_server_from_env
from examples.carousel_handler import CarouselWidgetHandler

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

# Create server with custom handler
server = create_server_from_env(
    message_handlers=[CarouselWidgetHandler()]
)

@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    """ChatKit protocol endpoint."""
    # Add user_id to context from session
    if "user_id" not in request.session:
        import uuid
        request.session["user_id"] = str(uuid.uuid4())

    context = {"user_id": request.session["user_id"]}
    return await server.handle_request(request, context)
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LANGGRAPH_API_URL` | LangGraph API base URL | Yes* | - |
| `LANGGRAPH_ASSISTANT_ID` | LangGraph assistant/graph ID | Yes* | - |
| `LANGGRAPH_TIMEOUT` | Request timeout in seconds | No | 60.0 |

*Required when using `create_server_from_env()`

### Constructor Parameters

```python
LangGraphChatKitServer(
    langgraph_url: str,              # LangGraph API URL
    assistant_id: str,               # Assistant/graph ID
    store: MemoryStore | None,       # Store implementation
    message_handlers: list[MessageHandler] | None,  # Custom handlers
    timeout: float = 60.0            # Request timeout
)
```

## Advanced Usage

### Custom Store Implementation

```python
from chatkit.store import Store
from chatkit_langgraph import LangGraphChatKitServer

class MyPersistentStore(Store):
    """Your PostgreSQL/Redis/etc implementation."""
    # Implement Store interface methods
    pass

server = LangGraphChatKitServer(
    langgraph_url="...",
    assistant_id="...",
    store=MyPersistentStore()
)
```

### Multiple Message Handlers

```python
server = LangGraphChatKitServer(
    langgraph_url="...",
    assistant_id="...",
    message_handlers=[
        WidgetHandler(),      # Check for widget triggers first
        CommandHandler(),     # Then check for commands
        RoutingHandler(),     # Then apply routing logic
        # Falls back to LangGraph if no handler claims the message
    ]
)
```

### Error Handling

The adapter provides comprehensive error handling:
- Network errors from LangGraph API
- Invalid thread IDs (auto-converts to UUID)
- Empty responses (fallback messages)
- Timeout handling
- Structured logging

## Development

### Project Structure

```
backend/
├── chatkit_langgraph/          # 📦 Main package (reusable)
│   ├── __init__.py
│   ├── client.py              # LangGraph API client
│   ├── server.py              # ChatKit server adapter
│   └── store.py               # Memory store implementation
├── examples/                   # 📚 Demo code (not in package)
│   ├── __init__.py
│   ├── carousel_handler.py    # Example widget handler
│   ├── custom_widgets.py      # Widget composition examples
│   └── widget_examples.py     # Pre-built widget examples
├── pyproject.toml             # Package metadata
└── README.md                  # This file
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black chatkit_langgraph/

# Lint
ruff check chatkit_langgraph/

# Type check
mypy chatkit_langgraph/
```

## API Reference

### LangGraphStreamClient

```python
client = LangGraphStreamClient(
    base_url: str,
    assistant_id: str = "agent",
    timeout: float = 60.0
)

# Stream responses
async for event in client.stream_response(
    thread_id: str | None,
    user_message: str
):
    # Process event
    ai_msg = client.extract_latest_ai_message(event)
    if client.is_final_response(event):
        break
```

### MessageHandler (Abstract)

```python
class MessageHandler(ABC):
    @abstractmethod
    async def should_handle(
        self,
        user_message: str,
        thread: ThreadMetadata,
        context: dict[str, Any]
    ) -> bool:
        """Return True if this handler should process the message."""
        pass

    @abstractmethod
    async def handle(
        self,
        user_message: str,
        thread: ThreadMetadata,
        context: dict[str, Any]
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Handle the message and yield ChatKit events."""
        pass
```

## FAQ

**Q: Can I use this with self-hosted LangGraph?**
A: Yes! Just point `langgraph_url` to your self-hosted instance.

**Q: Does this work with LangGraph Cloud?**
A: Yes! Works with any LangGraph deployment that exposes the streaming API.

**Q: Can I customize the threading behavior?**
A: Yes! The adapter auto-converts ChatKit thread IDs to UUIDs for LangGraph compatibility.

**Q: How do I add file upload support?**
A: Override `to_message_content()` in your server subclass.

**Q: Is the MemoryStore production-ready?**
A: No, it's for demos only. Replace with a persistent Store implementation for production.

**Q: Can I use this with other LLM providers?**
A: The adapter is LangGraph-specific, but you can implement a similar adapter for other providers.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Credits

Built with:
- [OpenAI ChatKit](https://platform.openai.com/docs/chatkit) - Chat UI framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent orchestration framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [httpx](https://www.python-httpx.org/) - Async HTTP client

## Support

- 📖 [Documentation](https://github.com/yourusername/chatkit-langgraph-adapter#readme)
- 🐛 [Issue Tracker](https://github.com/yourusername/chatkit-langgraph-adapter/issues)
- 💬 [Discussions](https://github.com/yourusername/chatkit-langgraph-adapter/discussions)
