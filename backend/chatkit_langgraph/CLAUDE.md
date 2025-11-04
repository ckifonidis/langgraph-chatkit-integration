# chatkit_langgraph

## Purpose
Core reusable adapter package that bridges OpenAI ChatKit with LangGraph API, providing server infrastructure, streaming client, and state management for building conversational interfaces powered by LangGraph agents.

## Key Files
- **`__init__.py`**: Package exports - `LangGraphChatKitServer`, `LangGraphStreamClient`, `MemoryStore`, `MessageHandler`, and `create_server_from_env()` factory
- **`server.py`**: Main ChatKit server implementation with extensible message handlers, widget rendering, and action processing
- **`client.py`**: LangGraph API streaming client that handles SSE parsing, thread management, and state event processing
- **`store.py`**: In-memory storage for threads, messages, user preferences (favorites/hidden), and property descriptions with user isolation
- **`description_client.py`**: AI-powered property description generator using OpenAI API

## Dependencies

### External
- `chatkit` (ChatKit SDK) - Server base class, types, and widget components
- `httpx` - Async HTTP client for LangGraph API streaming
- `pydantic` - Data validation and serialization for LangGraph events
- `openai` - OpenAI API client for description generation
- `fastapi` - Web framework (used by consuming applications)

### Internal
- None (leaf package, no internal dependencies)

## Architecture Notes

### Server Design Pattern
- **Extensibility via MessageHandler ABC**: Before routing to LangGraph, server checks registered handlers via `can_handle()` pattern, enabling keyword-triggered responses or custom logic
- **Component Registry Integration**: Server accepts `ComponentRegistry` to render widgets based on LangGraph response structure
- **Dependency Injection**: `create_server_from_env()` factory instantiates server with configuration from environment variables

### State Management
- **User Isolation**: All threads and preferences filtered by `user_id` from session context
- **Preferences Schema v3**: Thread-specific favorites and hidden properties stored as nested dicts `{user_id: {thread_id: {favorites: {}, hidden: {}}}}`
- **Historical Data Filtering**: `_apply_preferences_to_widgets()` applies current preferences to historical ListView widgets during `load_thread_items()`
- **Real-Time Widget Updates**: `_filter_listview_widget()` removes hidden properties and updates favorite icons in carousels
- **Global Description Cache**: Property descriptions shared across all users to reduce AI generation costs
- **Auto-Thread Creation**: Missing threads auto-created in `load_thread()` to prevent race conditions

### Streaming Architecture
- **SSE to ChatKit Events**: `LangGraphStreamClient` parses Server-Sent Events from LangGraph API and yields state updates
- **Buffered Response Pattern**: Server buffers all LangGraph events, extracts final AI message, then yields ChatKit `ThreadStreamEvent` instances
- **Coordinate Transformation**: Automatically converts LangGraph's `"lat,lng"` strings to GeoJSON `{"type": "Point", "coordinates": [lng, lat]}` format

### Action Handling
- **Silent Updates**: Widget actions (`toggle_favorite`, `hide_property`) update store without yielding events, applied on next query
- **Property Code-Based**: Actions use `propertyCode` payload for identifying targets
- **Thread Title Updates**: `update_thread_title` action persists custom titles to thread metadata

## Usage

### Creating a Server Instance
```python
from chatkit_langgraph import create_server_from_env

server = create_server_from_env(
    message_handlers=[CustomHandler()],
    component_registry=registry
)
```

### Integrating with FastAPI
```python
from fastapi import Depends, FastAPI
from chatkit_langgraph import LangGraphChatKitServer

app = FastAPI()

@app.post("/langgraph/chatkit")
async def chatkit_endpoint(
    server: LangGraphChatKitServer = Depends(get_server)
):
    # Server handles all ChatKit protocol messages
    return server.handle_request(...)
```

### Extending with Custom Handlers
```python
from chatkit_langgraph import MessageHandler

class KeywordHandler(MessageHandler):
    def can_handle(self, user_message: str, context: dict) -> bool:
        return "help" in user_message.lower()

    async def handle(self, thread, item, context):
        yield ThreadItemDoneEvent(...)
```

## Production Considerations
- **⚠️ MemoryStore is ephemeral**: Replace with PostgreSQL/Redis for production (threads/preferences lost on restart)
- **No Rate Limiting**: Implement throttling for LangGraph API calls
- **Session-Based Users**: Replace with proper authentication system
- **Description Cache Eviction**: No TTL on cached descriptions (unbounded memory growth)
