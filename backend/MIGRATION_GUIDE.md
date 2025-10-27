# Migration Guide: Old → New Structure

## Overview

The LangGraph→ChatKit adapter has been refactored into a **100% reusable package**. This guide shows how to migrate from the old structure to the new one.

## What Changed?

### Old Structure ❌
```
backend/app/
├── langgraph_chatkit_server.py  # Mixed library + demo code
├── langgraph_client.py           # Reusable
├── memory_store.py               # Reusable
├── custom_widgets.py             # Demo code
├── widget_examples.py            # Demo code
└── main.py                       # App entry point
```

**Problems:**
- Hard-coded widget logic in server
- Demo code mixed with library code
- Not distributable as a package
- Hard-coded default URLs

### New Structure ✅
```
backend/
├── chatkit_langgraph/              # 📦 Reusable package
│   ├── __init__.py
│   ├── client.py                   # LangGraph API client
│   ├── server.py                   # ChatKit server (extensible)
│   └── store.py                    # Memory store
├── examples/                       # 📚 Demo code (separate)
│   ├── __init__.py
│   ├── carousel_handler.py         # Example handler
│   ├── custom_widgets.py           # Widget examples
│   └── widget_examples.py          # Widget templates
├── app/
│   └── main.py                     # FastAPI app (uses package)
├── pyproject.toml                  # Package metadata
├── README.md                       # Package documentation
├── USAGE_EXAMPLES.md               # Usage examples
└── LICENSE                         # MIT license
```

**Benefits:**
- ✅ Clean separation of library vs demo code
- ✅ Fully extensible via MessageHandler
- ✅ No hard-coded logic
- ✅ Distributable as pip package
- ✅ Production-ready

## Migration Steps

### Step 1: Update Imports

**Old:**
```python
from .langgraph_chatkit_server import (
    LangGraphChatKitServer,
    create_langgraph_chatkit_server,
)
```

**New:**
```python
from chatkit_langgraph import LangGraphChatKitServer, create_server_from_env
from examples.carousel_handler import CarouselWidgetHandler
```

### Step 2: Update Server Creation

**Old:**
```python
server = create_langgraph_chatkit_server()  # Uses hard-coded defaults
```

**New:**
```python
# Option 1: From environment variables
server = create_server_from_env(
    message_handlers=[CarouselWidgetHandler()]
)

# Option 2: Explicit configuration
server = LangGraphChatKitServer(
    langgraph_url="https://your-api.com",
    assistant_id="your-assistant",
    message_handlers=[CarouselWidgetHandler()]
)
```

### Step 3: Move Custom Logic to Handlers

**Old (in server.py):**
```python
# Hard-coded in respond() method
if "carousel" in user_message.lower():
    carousel_widget = get_example_widget("products")
    yield ThreadItemDoneEvent(item=widget_item)
    return
```

**New (in custom handler):**
```python
from chatkit_langgraph import MessageHandler

class CarouselWidgetHandler(MessageHandler):
    async def should_handle(self, user_message, thread, context):
        return "carousel" in user_message.lower()

    async def handle(self, user_message, thread, context):
        carousel_widget = get_example_widget("products")
        yield ThreadItemDoneEvent(item=widget_item)
```

### Step 4: Update Environment Variables

**Required variables:**
```bash
LANGGRAPH_API_URL=https://your-langgraph-api.com  # Required!
LANGGRAPH_ASSISTANT_ID=your-assistant-id          # Required!
LANGGRAPH_TIMEOUT=60.0                            # Optional
SESSION_SECRET_KEY=your-secret-key                # For sessions
```

## API Changes

### LangGraphChatKitServer

**Old:**
```python
LangGraphChatKitServer(
    langgraph_url: str | None = None,  # Had hard-coded default
    assistant_id: str | None = None,   # Had hard-coded default
)
```

**New:**
```python
LangGraphChatKitServer(
    langgraph_url: str,                # Required!
    assistant_id: str,                 # Required!
    store: MemoryStore | None = None,
    message_handlers: list[MessageHandler] | None = None,
    timeout: float = 60.0
)
```

### Factory Function

**Old:**
```python
create_langgraph_chatkit_server(
    langgraph_url: str | None = None,
    assistant_id: str | None = None,
) -> LangGraphChatKitServer
```

**New:**
```python
create_server_from_env(
    store: MemoryStore | None = None,
    message_handlers: list[MessageHandler] | None = None,
) -> LangGraphChatKitServer
```

## Backward Compatibility

The old files in `app/` directory are kept for backward compatibility:
- `app/langgraph_chatkit_server.py` (old server)
- `app/langgraph_client.py` (old client)
- `app/memory_store.py` (old store)

**You can:**
1. Delete them once you've migrated
2. Keep them for reference
3. Use them if you need the old behavior

**Recommendation:** Migrate to the new structure and delete old files.

## Benefits of New Structure

1. **Extensibility**
   - Add custom handlers without modifying core code
   - Multiple handlers can be chained
   - Clean separation of concerns

2. **Reusability**
   - Install as a package: `pip install .`
   - Use in multiple projects
   - Distribute to PyPI

3. **Testability**
   - Pure functions, no hard-coded state
   - Easy to mock handlers
   - Unit test friendly

4. **Maintainability**
   - Clear structure
   - Library code separate from demo code
   - Type hints throughout

5. **Production-Ready**
   - Comprehensive error handling
   - Structured logging
   - No hard-coded defaults

## Example Migration

### Before (app/langgraph_chatkit_server.py)

```python
class LangGraphChatKitServer(ChatKitServer):
    def __init__(self, langgraph_url=None, assistant_id=None):
        # Hard-coded default URL
        self.langgraph_url = langgraph_url or os.getenv(
            "LANGGRAPH_API_URL",
            "https://hard-coded-url.com"  # ❌ Not reusable
        )

    async def respond(self, thread, item, context):
        # Hard-coded widget logic
        if "carousel" in user_message:  # ❌ Mixed concerns
            yield carousel_widget
            return
        # ... LangGraph logic
```

### After (chatkit_langgraph/server.py + examples/carousel_handler.py)

**Library code (chatkit_langgraph/server.py):**
```python
class LangGraphChatKitServer(ChatKitServer):
    def __init__(
        self,
        langgraph_url: str,  # ✅ Required
        assistant_id: str,   # ✅ Required
        message_handlers: list[MessageHandler] | None = None,  # ✅ Extensible
    ):
        if not langgraph_url:
            raise ValueError("langgraph_url is required")  # ✅ Explicit

        self.message_handlers = message_handlers or []

    async def respond(self, thread, item, context):
        # Check handlers first
        for handler in self.message_handlers:  # ✅ Extensible
            if await handler.should_handle(user_message, thread, context):
                async for event in handler.handle(...):
                    yield event
                return

        # Fall back to LangGraph
        async for event in self._handle_with_langgraph(...):
            yield event
```

**Demo code (examples/carousel_handler.py):**
```python
class CarouselWidgetHandler(MessageHandler):  # ✅ Separate
    async def should_handle(self, user_message, thread, context):
        return "carousel" in user_message.lower()

    async def handle(self, user_message, thread, context):
        yield carousel_widget
```

## Testing the Migration

```bash
# 1. Update imports
# 2. Test the app
cd backend
python -m uvicorn app.main:app --reload --port 8004

# 3. Test in chat
# Send: "show me a carousel"
# Should work with new structure!

# 4. Verify environment variables
echo $LANGGRAPH_API_URL
echo $LANGGRAPH_ASSISTANT_ID
```

## Troubleshooting

### Error: "langgraph_url is required"
**Solution:** Set `LANGGRAPH_API_URL` environment variable or pass explicitly to constructor.

### Error: "Cannot import chatkit_langgraph"
**Solution:** Make sure you're running from the `backend/` directory or install the package:
```bash
cd backend
pip install -e .
```

### Error: "CarouselWidgetHandler not found"
**Solution:** The examples are in the `examples/` directory, not in the package. Import from `examples.carousel_handler`.

## Summary

| Feature | Old | New |
|---------|-----|-----|
| Structure | Monolithic | Modular |
| Extensibility | Hard-coded | MessageHandler pattern |
| Reusability | Project-specific | Pip-installable package |
| Defaults | Hard-coded URLs | Required config |
| Demo code | Mixed in | Separate examples/ |
| Distribution | Not possible | Ready for PyPI |
| Production | Not ready | Production-ready |

**Recommendation:** ✅ Migrate to new structure for all future development!
