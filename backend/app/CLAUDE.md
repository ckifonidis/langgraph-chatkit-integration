# app

## Purpose
FastAPI application entrypoint that wires together the ChatKit-LangGraph adapter, custom components, and HTTP endpoints, providing the main API server for the chat interface.

## Key Files
- **`main.py`**: FastAPI application with ChatKit endpoint, session middleware, component registration, and preference/description management endpoints
- **`__init__.py`**: Empty package marker

## Dependencies

### External
- `fastapi` - Web framework and HTTP server
- `starlette.middleware.sessions` - Session management for user isolation
- `fastapi.middleware.cors` - CORS configuration for local development
- `pydantic` - Request/response models (`GenerateDescriptionRequest`)

### Internal
- `../chatkit_langgraph` - Core adapter (`LangGraphChatKitServer`, `create_server_from_env`)
- `../custom_components` - Widget system (`ComponentRegistry`, `PropertyCarouselComponent`, `FiltersCardComponent`)

## Architecture Notes

### Application Initialization
- **Python Path Adjustment**: Adds `backend/` to `sys.path` for clean imports (lines 12-14)
- **Middleware Stack**: SessionMiddleware → CORS → Route handlers
- **Dependency Injection**: `get_langgraph_server()` provides singleton server instance to endpoints

### Session Management
- **User ID Assignment**: Auto-generates UUID for new sessions (`request.session["user_id"]`)
- **Cookie Configuration**: 30-day max age, lax same-site policy, session cookie name: `chatkit_session`
- **⚠️ Development Mode**: `https_only=False` and `SESSION_SECRET_KEY` default to insecure values

### Component Registration
```python
component_registry = ComponentRegistry()
component_registry.register(FiltersCardComponent())
component_registry.register(PropertyCarouselComponent(max_items=50))
```
Components auto-render based on LangGraph response structure.

### Endpoint Architecture

#### Core ChatKit Protocol
- **`POST /langgraph/chatkit`**: Main endpoint handling all ChatKit messages (`threads.list`, `messages.create`, etc.)
  - Accepts raw request body, processes via `server.process(payload, context)`
  - Returns SSE stream (`StreamingResult`) or JSON response
  - Injects `user_id` from session into context

#### Health & Monitoring
- **`GET /langgraph/health`**: Returns status + LangGraph API configuration

#### Thread-Specific Preferences API
- **`GET /langgraph/preferences?thread_id=X`**: Fetch favorites/hidden for specific thread
- **`POST /langgraph/preferences/favorites`**: Add property to thread favorites (body: `{thread_id, propertyCode, propertyData}`)
- **`DELETE /langgraph/preferences/favorites/{code}?thread_id=X`**: Remove from thread favorites
- **`POST /langgraph/preferences/hidden`**: Hide property in thread (body: `{thread_id, propertyCode, propertyData}`)
- **`DELETE /langgraph/preferences/hidden/{code}?thread_id=X`**: Unhide property in thread

#### AI Description Generation
- **`POST /langgraph/generate-description`**: Generate property descriptions via second LangGraph API
  - Checks global cache first (`server.store.get_global_description()`)
  - If miss: calls `DescriptionLangGraphClient.generate_description()`
  - Caches result globally across all users
  - Requires `LANGGRAPH_DESCRIPTION_API_URL` environment variable

## Usage

### Starting the Server
```bash
# From backend/ directory
uv run uvicorn app.main:app --reload --port 8004

# From project root (recommended)
.venv/bin/python -m uvicorn app.main:app --reload --port 8004
```

### Environment Variables
```bash
LANGGRAPH_API_URL=https://your-langgraph-api.com
LANGGRAPH_ASSISTANT_ID=agent
SESSION_SECRET_KEY=<secrets.token_hex(32)>
LANGGRAPH_DESCRIPTION_API_URL=https://description-api.com  # Optional
LANGGRAPH_DESCRIPTION_ASSISTANT_ID=agent  # Default: "agent"
LANGGRAPH_DESCRIPTION_TIMEOUT=30  # Default: 30 seconds
```

### API Usage Examples

#### Health Check
```bash
curl http://localhost:8004/langgraph/health
# → {"status": "healthy", "langgraph_url": "...", "assistant_id": "agent"}
```

#### Get Thread Preferences
```bash
curl "http://localhost:8004/langgraph/preferences?thread_id=thr_abc123" \
  --cookie "chatkit_session=..."
# → {"user_id": "12345678", "thread_id": "thr_abc123", "preferences": {...}}
```

#### Add Favorite
```bash
curl -X POST http://localhost:8004/langgraph/preferences/favorites \
  -H "Content-Type: application/json" \
  --cookie "chatkit_session=..." \
  -d '{
    "thread_id": "thr_abc123",
    "propertyCode": "PROP001",
    "propertyData": {"code": "PROP001", "title": "..."}
  }'
```

#### Generate Description
```bash
curl -X POST http://localhost:8004/langgraph/generate-description \
  -H "Content-Type: application/json" \
  -d '{
    "propertyCode": "00000527",
    "propertyData": {...},
    "language": "english"
  }'
# → {"description": "...", "cached": false, "propertyCode": "00000527"}
```

## Request Flow

### ChatKit Message Flow
```
Client → POST /langgraph/chatkit
       ↓
Session middleware assigns user_id
       ↓
server.process(payload, {request, user_id})
       ↓
LangGraphChatKitServer routes to handler
       ↓
ComponentRegistry.get_widgets(response, preferences)
       ↓
StreamingResponse (SSE) → Client
```

### Preference Management Flow
```
Client → POST /preferences/favorites
       ↓
Session middleware extracts user_id
       ↓
server.store.add_favorite(user_id, code, data, thread_id)
       ↓
Return updated preferences for thread
       ↓
Client receives {"success": true, "preferences": {...}}
```

## Production Considerations
- **⚠️ CORS Wide Open**: `allow_origins=["*"]` - restrict to specific domains
- **⚠️ Session Security**: Set `SESSION_SECRET_KEY` to `secrets.token_hex(32)`, enable `https_only=True`
- **⚠️ No Rate Limiting**: Add throttling middleware for `/langgraph/chatkit` and description endpoint
- **⚠️ MemoryStore**: Replace with PostgreSQL/Redis for persistence
- **Error Handling**: All endpoints return 500 on exceptions - consider structured error responses
- **Logging**: Add request ID tracking and structured logging
- **Metrics**: Instrument endpoints with Prometheus/OpenTelemetry
