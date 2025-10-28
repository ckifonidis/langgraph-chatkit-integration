# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LangGraph ChatKit Integration - A FastAPI backend that integrates ChatKit (OpenAI's chat UI framework) with LangGraph API, enabling rich conversational interfaces powered by custom LangGraph agents.

**Key Technologies:**
- Backend: FastAPI, Python 3.11+, ChatKit SDK, LangGraph API Client
- Frontend: React 19, TypeScript, Vite, ChatKit React Components
- Infrastructure: Docker, uvicorn

## Development Commands

### Backend Development
```bash
# Start backend server (from project root)
cd backend
uv run uvicorn app.main:app --reload --port 8004

# Alternative with system Python
python3 -m uvicorn app.main:app --reload --port 8004

# Run from project root (recommended pattern per logs)
.venv/bin/python -m uvicorn app.main:app --reload --port 8004
```

### Frontend Development
```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server (port 5174)
npm run build        # Production build
npm run lint         # Run ESLint
```

### Full Stack Development
```bash
# From project root - starts both backend and frontend
npm start
```

### Docker Deployment
```bash
# Build and run with docker-compose
docker-compose up --build

# Access at http://localhost:8080
```

### Testing
```bash
# Health check
curl http://localhost:8004/langgraph/health

# No automated test suite currently exists
# Test file found: backend/test_e2e.py (may be outdated)
```

## Architecture

### High-Level Flow
```
User → ChatKit React UI → FastAPI Backend → LangGraph API
         ↑                       ↓                 ↓
         └─── SSE Streaming ─────┴─── Events ─────┘
```

### Backend Architecture (`backend/`)

**Core Modules:**

1. **`app/main.py`** - FastAPI application entrypoint
   - Single endpoint: `POST /langgraph/chatkit` (handles all ChatKit protocol messages)
   - Session middleware for per-user thread isolation
   - Dependency injection pattern for server initialization
   - CORS configuration for local development

2. **`chatkit_langgraph/`** - Reusable adapter package
   - `server.py`: `LangGraphChatKitServer` - Main ChatKit server with extensible message handlers
   - `client.py`: `LangGraphStreamClient` - Streams events from LangGraph API
   - `store.py`: `MemoryStore` - Thread/message persistence with user filtering
   - `__init__.py`: Exports + `create_server_from_env()` factory function

3. **`custom_components/`** - Rule-based widget rendering system
   - `base.py`: `CustomComponent` abstract base class
   - `__init__.py`: `ComponentRegistry` for managing components
   - `property_carousel.py`: Auto-renders carousel when `query_results` exists
   - `property_detail.py`: Detailed property view on drilldown
   - Components automatically activate based on LangGraph response structure

4. **`examples/`** - Demonstration handlers and widgets
   - `carousel_handler.py`: `CarouselWidgetHandler` - Demo message handler
   - `custom_widgets.py`: Low-level widget builder functions
   - `widget_examples.py`: Widget creation examples

### Key Design Patterns

**1. Message Handlers** (`chatkit_langgraph/server.py`)
```python
class MessageHandler(ABC):
    def can_handle(self, user_message: str, context: dict) -> bool
    async def handle(self, thread, item, context) -> AsyncIterator[ThreadStreamEvent]
```
Handlers intercept messages BEFORE LangGraph, enabling custom responses for keywords.

**2. Custom Components** (`custom_components/`)
```python
class CustomComponent(ABC):
    def check_rules(self, response_data: dict) -> bool  # When to render
    def render(self, response_data: dict) -> Card       # How to render
    def get_priority(self) -> int                       # Render order
```
Components automatically render widgets based on LangGraph response structure.

**3. Dependency Injection**
Server initialization uses dependency injection pattern:
```python
_langgraph_server = create_server_from_env(
    message_handlers=[...],
    component_registry=registry
)

@app.post("/langgraph/chatkit")
async def chatkit_endpoint(
    server: LangGraphChatKitServer = Depends(get_langgraph_server)
)
```

**4. Session-Based User Isolation**
```python
# User ID assigned via session middleware
request.session["user_id"] = str(uuid.uuid4())
# Threads filtered by user_id in MemoryStore.load_threads()
```

### Frontend Architecture (`frontend/src/`)

- Standard ChatKit React integration
- Main component: `ChatKitPanel.tsx` (likely location)
- Widget action handlers configured via `widgets.onAction`
- Connects to `/langgraph/chatkit` endpoint

## Environment Configuration

Required variables (see `.env.example`):
```bash
LANGGRAPH_API_URL=https://your-langgraph-api.com
LANGGRAPH_ASSISTANT_ID=agent  # LangGraph graph/assistant ID
SESSION_SECRET_KEY=<generate-with-secrets.token_hex(32)>
VITE_LANGGRAPH_CHATKIT_API_DOMAIN_KEY=<chatkit-domain-key>
```

## ChatKit Protocol Implementation

The `/langgraph/chatkit` endpoint handles these message types:
- `threads.list` - Get user's thread history (filtered by session user_id)
- `threads.create` - Create new thread (format: `thr_<8char_hex>`)
- `messages.create` - Send message, streams back SSE events
- `items.retry` - Regenerate assistant response
- Widget actions via `action()` method

All responses use Server-Sent Events (SSE) with `text/event-stream`.

## Custom Components System

**How It Works:**
1. LangGraph returns response (e.g., `{"query_results": [...]}`)
2. ComponentRegistry checks each component's `check_rules(response_data)`
3. Matching components render widgets via `render(response_data)`
4. Widgets are yielded as `ThreadItemDoneEvent` items
5. ChatKit UI displays widgets automatically

**Adding New Components:**
1. Create class inheriting from `CustomComponent`
2. Implement `check_rules()` - return True when component should activate
3. Implement `render()` - return ChatKit widget (usually `Card`)
4. Register in `app/main.py`: `component_registry.register(MyComponent())`

**Example Use Case:**
PropertyCarouselComponent activates when response contains `query_results` array and automatically renders a horizontal scrollable carousel of properties.

## Widget System

ChatKit provides 25+ widget types that compose into rich UIs:
- Containers: Card, Row, Col, Box, ListView, Form
- Interactive: Button, Input, Select, Checkbox, RadioGroup
- Display: Text, Title, Image, Icon, Badge, Markdown

Widgets are created in Python backend using `chatkit.widgets` classes and automatically render in React frontend.

## Code Organization Principles

1. **Backend modules** in `backend/` directory with Python path adjustments in `app/main.py`
2. **Separation of concerns**: Core adapter (`chatkit_langgraph/`) vs application code (`app/`) vs extensions (`custom_components/`, `examples/`)
3. **Factory pattern**: Use `create_server_from_env()` for server initialization
4. **Extension points**: Message handlers, component registry, widget actions
5. **Thread isolation**: All thread operations filtered by `user_id` from session

## Common Development Scenarios

### Adding a New Message Handler
1. Create class inheriting from `MessageHandler` in `examples/` or `app/`
2. Implement `can_handle()` and `handle()` methods
3. Register in `app/main.py`: `create_server_from_env(message_handlers=[YourHandler()])`

### Adding Custom Widget Logic
1. For keyword-triggered widgets → Use MessageHandler
2. For response-based widgets → Use CustomComponent
3. For reusable widget builders → Add to `examples/custom_widgets.py`

### Debugging Widget Issues
- Check browser console for ChatKit validation errors
- Verify widget structure with `assert widget is not None`
- Check SSE stream with: `curl -N http://localhost:8004/langgraph/chatkit`
- Enable logging: `logger.info()` in server code

### Working with LangGraph Responses
LangGraph responses are buffered and passed to:
1. Message handlers (full response access)
2. Custom components (via `response_data` parameter)
3. Widget builders (as needed)

Typical structure: `{"messages": [...], "query_results": [...], "sql_query": {...}}`

## Important File Locations

- Backend entrypoint: `backend/app/main.py:69` (chatkit_endpoint)
- Server initialization: `backend/app/main.py:54` (_langgraph_server)
- Component registry: `backend/app/main.py:49-51`
- LangGraph response handling: `backend/chatkit_langgraph/server.py` (respond method)
- Widget action handling: `backend/chatkit_langgraph/server.py` (action method)
- Thread storage: `backend/chatkit_langgraph/store.py`
- Custom component base: `backend/custom_components/base.py`

## Production Considerations

- Replace MemoryStore with persistent storage (PostgreSQL/Redis)
- Set `SESSION_SECRET_KEY` to cryptographically secure value
- Enable `https_only=True` for SessionMiddleware
- Update CORS `allow_origins` to specific domains
- Implement rate limiting on `/langgraph/chatkit` endpoint
- Add monitoring and health checks
- Review `DOCUMENTATION.md` for security checklist

## Documentation

- `README.md` - Quick start and basic setup
- `DOCUMENTATION.md` - Comprehensive guide (1200+ lines) covering protocol, widgets, best practices
- `VERIFICATION_SUMMARY.md` - Implementation verification notes
- `custom_components/README.md` - Complete component system guide
- `examples/DRILLDOWN_USAGE.md` - Carousel drilldown feature guide
