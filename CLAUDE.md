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
   - `property_carousel.py`: Auto-renders ListView when `query_results` exists
   - `widgets.py`: Reusable widget functions (`create_property_listview`, `create_favorite_button`, `create_hide_button`)
   - Components automatically activate based on LangGraph response structure

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

## User Preferences System

The application includes a user preferences system that allows users to favorite and hide properties. Preferences are stored per-user session and persist for the session duration.

### Architecture

**Storage (`backend/chatkit_langgraph/store.py`):**
- Preferences stored in `MemoryStore._preferences` dict: `{user_id: {favorites: [], hidden: [], version: 1}}`
- Methods: `get_preferences()`, `add_favorite()`, `remove_favorite()`, `hide_property()`, `unhide_property()`

**UI Components (`backend/custom_components/widgets.py`):**
- `create_favorite_button()` - Star icon button (filled when favorited)
- `create_hide_button()` - Eye-slash icon button
- Both buttons emit server-side actions (no handler specified, defaults to server)

**Action Handling (`backend/chatkit_langgraph/server.py`):**
- `action()` method handles `toggle_favorite` and `hide_property` actions
- Updates preferences silently (no immediate UI re-render)
- Preferences are applied on next property search/query

### How It Works

**1. User Clicks Favorite Button:**
```
User clicks star → toggle_favorite action → server.action()
                 ↓
         Updates MemoryStore preferences
                 ↓
         No immediate response (silent update)
                 ↓
         Next search uses updated preferences
```

**2. Filtering Properties:**
```python
# In property_carousel.py render() method:
properties = response_data.get("query_results", [])

# Filter out hidden properties
if user_preferences:
    hidden = user_preferences.get('hidden', [])
    if hidden:
        properties = [
            prop for prop in properties
            if prop.get('code') not in hidden
        ]

# Display favorite status
favorites = user_preferences.get('favorites', [])
# Used to show filled/unfilled star icons
```

**3. Server-Side Flow:**
```python
# server.py action() method
async def action(...) -> AsyncIterator[ThreadStreamEvent]:
    user_id = context.get("user_id", "anonymous")

    if action.type == "toggle_favorite":
        property_code = action.payload.get("propertyCode")
        prefs = self.store.get_preferences(user_id)
        if property_code in prefs['favorites']:
            self.store.remove_favorite(user_id, property_code)
        else:
            self.store.add_favorite(user_id, property_code)

    # No events yielded - silent update
```

### Implementation Details

**Button Configuration:**
```python
# Favorite button (widgets.py:645-673)
Button(
    label="",  # Icon only
    iconStart="star-filled" if is_favorited else "star",
    color="warning" if is_favorited else "secondary",
    onClickAction=ActionConfig(
        type="toggle_favorite",
        payload={"propertyCode": property_code}
        # No handler specified - defaults to server-side
    )
)

# Hide button (widgets.py:676-700)
Button(
    label="",  # Icon only
    iconStart="empty-circle",  # Substitute for eye-slash
    color="secondary",
    onClickAction=ActionConfig(
        type="hide_property",
        payload={"propertyCode": property_code}
    )
)
```

**User Preferences Structure:**
```python
{
    'favorites': {
        'PROP001': { # Full property object
            'code': 'PROP001',
            'title': 'Maisonette 224sqm, Nea Fokea',
            'price': 115000,
            'propertyArea': 224,
            'defaultImagePath': 'https://...',
            'address': {'prefecture': 'Chalkidiki'},
            # ... complete property data
        }
    },
    'hidden': {
        'PROP999': { # Full property object
            # ... complete property data
        }
    },
    'version': 2  # Schema version (v2 = dict-based, v1 = list-based)
}
```

**Loading Preferences in Response Handler:**
```python
# server.py _handle_with_langgraph() method
user_id = context.get("user_id", "anonymous")
user_preferences = self.store.get_preferences(user_id)

# Pass to component registry
widgets = self.component_registry.get_widgets(
    final_event,
    user_preferences=user_preferences
)
```

### Production Considerations

**Current Implementation (MemoryStore):**
- ⚠️ Preferences lost on server restart
- ⚠️ Not shared across multiple server instances
- ⚠️ No persistence beyond session lifetime

**Production Requirements:**
- Replace `MemoryStore` with persistent storage (PostgreSQL, Redis)
- Store preferences in database table: `user_preferences(user_id, favorites_json, hidden_json, updated_at)`
- Consider caching layer for frequently accessed preferences
- Add preference export/import functionality
- Implement preference limits (e.g., max 100 favorites)

**Example Database Schema:**
```sql
CREATE TABLE user_preferences (
    user_id VARCHAR(255) PRIMARY KEY,
    favorites JSONB DEFAULT '{}'::jsonb,
    hidden JSONB DEFAULT '{}'::jsonb,
    version INTEGER DEFAULT 2,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
```

### Preferences Sidebar

A right sidebar panel displays user preferences with full property cards:

**Features:**
- **Collapsed State** (default): Shows summary "X favorites • Y hidden"
- **Expanded State**: Displays full property cards with images, titles, prices
- **Auto-Refresh**: Updates every 5 seconds to catch server-side changes
- **Responsive**: Hidden on mobile, visible on medium+ screens

**Implementation:**
- `PreferencesContext.tsx` - React Context providing preferences state and refresh function
- `PreferencesSidebar.tsx` - Collapsible sidebar component with property cards
- `Home.tsx` - Renders sidebar above header in right section
- `ChatKitPanel.tsx` - Polls `/langgraph/preferences` every 5 seconds
- `App.tsx` - Wrapped with `<PreferencesProvider>`

**Endpoints:**
- `GET /langgraph/preferences` - Returns current user's preferences with full property data

**File Locations:**
- Context: `frontend/src/contexts/PreferencesContext.tsx`
- Sidebar: `frontend/src/components/PreferencesSidebar.tsx`

## Widget System

ChatKit provides 25+ widget types that compose into rich UIs:
- Containers: Card, Row, Col, Box, ListView, Form
- Interactive: Button, Input, Select, Checkbox, RadioGroup
- Display: Text, Title, Image, Icon, Badge, Markdown

Widgets are created in Python backend using `chatkit.widgets` classes and automatically render in React frontend.

## Code Organization Principles

1. **Backend modules** in `backend/` directory with Python path adjustments in `app/main.py`
2. **Separation of concerns**: Core adapter (`chatkit_langgraph/`) vs application code (`app/`) vs extensions (`custom_components/`)
3. **Factory pattern**: Use `create_server_from_env()` for server initialization
4. **Extension points**: Message handlers, component registry, widget actions
5. **Thread isolation**: All thread operations filtered by `user_id` from session
6. **User preferences**: Per-session favorites and hidden properties stored in MemoryStore

## Common Development Scenarios

### Adding a New Message Handler
1. Create class inheriting from `MessageHandler` in `app/` or new module
2. Implement `should_handle()` and `handle()` methods
3. Register in `app/main.py`: `create_server_from_env(message_handlers=[YourHandler()])`

### Adding Custom Widget Logic
1. For keyword-triggered widgets → Use MessageHandler
2. For response-based widgets → Use CustomComponent
3. For reusable widget builders → Add to `custom_components/widgets.py`

### Working with User Preferences
1. Get preferences: `user_preferences = self.store.get_preferences(user_id)`
2. Update favorites: `self.store.add_favorite(user_id, property_code)` or `self.store.remove_favorite(user_id, property_code)`
3. Hide/unhide properties: `self.store.hide_property(user_id, property_code)` or `self.store.unhide_property(user_id, property_code)`
4. Filter results: Check `property_code not in user_preferences.get('hidden', [])` in component render methods

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

- Backend entrypoint: `backend/app/main.py` (chatkit_endpoint)
- Server initialization: `backend/app/main.py` (_langgraph_server, component_registry)
- LangGraph response handling: `backend/chatkit_langgraph/server.py` (respond method, _handle_with_langgraph method)
- Widget action handling: `backend/chatkit_langgraph/server.py` (action method - handles toggle_favorite, hide_property)
- Thread & preference storage: `backend/chatkit_langgraph/store.py` (MemoryStore class)
- Custom component base: `backend/custom_components/base.py` (CustomComponent ABC)
- Property carousel component: `backend/custom_components/property_carousel.py` (PropertyCarouselComponent)
- Widget builders: `backend/custom_components/widgets.py` (create_property_listview, create_favorite_button, create_hide_button)
- Frontend ChatKit panel: `frontend/src/components/ChatKitPanel.tsx` (widget action handlers, property detail modal)
- Property detail modal: `frontend/src/components/PropertyDetailModal.tsx` (client-side property details)

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
- `CLAUDE.md` - This file - development guide and architecture overview
