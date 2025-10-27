# ChatKit Protocol Analysis

## Overview
This document captures the findings from analyzing the ChatKit Studio playground to understand what needs to be implemented in our middleware for full ChatKit compatibility.

## Key Findings from Playground Analysis

### 1. Primary API Endpoint
- **Endpoint**: POST to `/chatkit` (in our case: `/langgraph/chatkit`)
- **Content-Type**: `application/json` or Server-Sent Events (SSE)
- **Purpose**: Single endpoint handles all ChatKit protocol messages

### 2. ChatKit Protocol Message Types

Based on the playground exploration, ChatKit uses a message-based protocol where the client sends different message types to the server:

#### Message Type: `threads.list`
**Request Format:**
```json
{
  "type": "threads.list",
  "params": {
    "limit": 9999,
    "order": "desc"
  }
}
```

**Expected Response:**
```json
{
  "data": [
    {
      "id": "thr_d962848b",
      "created_at": "2025-10-24T12:28:32.205816",
      "status": {
        "type": "active"
      },
      "metadata": {},
      "items": {
        "data": [],
        "has_more": false
      }
    }
  ],
  "has_more": false
}
```

**Current Issue**:
- Our implementation returns ALL threads from ALL users
- **FIXED**: We now filter by `user_id` from session context

#### Message Type: `threads.create`
**Purpose**: Create a new conversation thread

**Expected Behavior**:
- Creates a new thread with a unique ID (format: `thr_<8char_hex>`)
- Associates thread with current user session
- Returns thread metadata

#### Message Type: `messages.create`
**Purpose**: Send a user message and get AI response

**Expected Behavior**:
- Accepts user message content
- Streams response back as Server-Sent Events (SSE)
- Updates thread items with message history

### 3. Thread Structure

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

### 4. Thread Item Structure

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
}
```

### 5. User Session Management

**Current Implementation**:
```python
# In main.py - chatkit_endpoint
if "user_id" not in request.session:
    import uuid
    request.session["user_id"] = str(uuid.uuid4())

user_id = request.session["user_id"]
```

**Session Cookie Configuration**:
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

### 6. ChatKit UI Configuration

The playground shows ChatKit is configured via URL parameters (base64 encoded):

**Key Configuration Options**:
- `api.url`: Backend endpoint URL
- `api.domainKey`: ChatKit domain key for authentication
- `theme`: Color scheme, typography, radius, density
- `startScreen`: Greeting message and starter prompts
- `composer`: Placeholder text, disclaimer, attachments
- `tools`: Client-side tools configuration
- `threadItemActions`: Feedback and retry buttons

### 7. Network Requests Observed

#### Initial Page Load:
1. `GET /playground` - Load playground HTML
2. `GET chatkit.js` - Load ChatKit library
3. `POST /v1/chatkit/domain_keys/verify` - Verify domain key
4. `POST /chatkit` - Initial connection

#### User Interaction:
1. Click starter prompt → `POST /chatkit` (send message)
2. Stream response via SSE
3. Click "Conversation history" → `POST /chatkit` (threads.list)
4. Click "New chat" → Local state change (no API call for creation until first message)

### 8. Required Middleware Features

#### ✅ Already Implemented:
1. Session-based user identification
2. Per-user thread filtering in `MemoryStore.load_threads()`
3. User-thread association in `MemoryStore.save_thread()`
4. Thread cleanup in `MemoryStore.delete_thread()`

#### 🔄 Needs Verification:
1. **Message History Pagination**:
   - Support `after` parameter in threads.list
   - Support `limit` parameter
   - Handle `has_more` flag correctly

2. **Thread Metadata**:
   - Store custom metadata per thread
   - Return metadata in thread list

3. **Thread Status Management**:
   - Support "active" vs "archived" status
   - Allow status updates

4. **Message Streaming**:
   - Verify SSE format matches ChatKit expectations
   - Ensure proper event types are sent

#### ❌ Not Yet Implemented:
1. **Thread Title Generation**:
   - Auto-generate thread titles from first message
   - Update thread metadata with title

2. **Message Feedback**:
   - Handle thumbs up/down feedback
   - Store feedback in thread item metadata

3. **Message Retry**:
   - Support regenerating last assistant message
   - Handle retry requests

4. **Client-Side Tools**:
   - Parse and execute client-side tool calls
   - Return tool results to frontend

## API Endpoint Patterns

### Pattern 1: Request-Response (JSON)
Used for: Creating threads, listing threads, updating metadata

**Request**:
```http
POST /langgraph/chatkit
Content-Type: application/json

{
  "type": "threads.list",
  "params": { ... }
}
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": [...],
  "has_more": false
}
```

### Pattern 2: Streaming Response (SSE)
Used for: Message responses, real-time updates

**Request**:
```http
POST /langgraph/chatkit
Content-Type: application/json

{
  "type": "messages.create",
  "thread_id": "thr_abc123",
  "message": { ... }
}
```

**Response**:
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: thread.item.delta
data: {"delta": ...}

event: thread.item.done
data: {"item": ...}
```

## Implementation Checklist

### High Priority (Core Functionality)
- [x] User session management with cookies
- [x] Per-user thread filtering
- [x] Thread creation with user association
- [x] Basic message handling
- [x] SSE streaming responses

### Medium Priority (Enhanced UX)
- [ ] Thread title auto-generation
- [ ] Proper pagination support
- [ ] Thread archiving/status management
- [ ] Message feedback storage
- [ ] Message retry functionality

### Low Priority (Advanced Features)
- [ ] Client-side tool execution
- [ ] File attachment handling
- [ ] Custom metadata persistence
- [ ] Thread search/filtering
- [ ] Export thread history

## Testing Recommendations

1. **Multi-User Testing**:
   - Open app in different browsers
   - Verify thread isolation
   - Check session persistence

2. **Thread List Testing**:
   - Create multiple threads per user
   - Verify ordering (desc by created_at)
   - Test pagination with large thread counts

3. **Message Flow Testing**:
   - Send messages in different threads
   - Verify responses stream correctly
   - Check message history persistence

4. **Session Persistence Testing**:
   - Close and reopen browser
   - Verify sessions persist (30 day cookie)
   - Test session expiration

## Widgets Discovery

### Widget Structure
Widgets are interactive UI components that can be embedded in assistant messages. Based on the playground exploration:

**Widget Types Observed**:
1. **ListView Widget** - Shows a list of options (e.g., Email, Calendar, Tasks widgets)
2. **Email Widget** - Interactive email composer with actions
3. **Calendar Widget** - Calendar event management
4. **Tasks Widget** - Task/todo management

**Widget Actions**:
```javascript
// Logged when widget is clicked
ChatKit log: widget.action {
  widgetType: "ListView",
  actionType: "sample.show_widget",
  handler: "server"
}
```

**Widget Response Format** (inferred from network requests):
- Widgets fetch icons/assets from backend
- Widget states can be updated via actions
- Actions can be handled server-side or client-side

**Implementation Notes**:
- Our backend needs to support widget definitions in message responses
- Widget actions need to be handled in the `onClientTool` callback (for client-side)
- Server-side widget actions require backend endpoint handling

## Client-Side Tools Discovery

### Tool Activation Flow
1. User clicks tool icon in composer ('+' button)
2. Menu appears showing available tools
3. Clicking a tool activates it and changes composer placeholder

**Tools Observed**:
- **Search docs** - Changes placeholder to "Search documentation"
- **Create theme** - Custom tool for theme creation
- **Add photos & files** - File attachment handling

**Console Logs**:
```javascript
ChatKit log: composer.tool.select {
  toolId: "search_docs",
  source: "toolMenu"
}
```

**Visual Indicators**:
- Active tool shows a badge in composer (e.g., "Docs 📘 ✕")
- Badge can be clicked to deactivate tool
- Placeholder text changes based on active tool

**Implementation Requirements**:
```typescript
// Frontend configuration
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

// Backend handling (in onClientTool callback)
onClientTool: async (invocation) => {
  if (invocation.name === "search_docs") {
    // Handle search logic
    return { success: true, result: ... };
  }
}
```

## Console Event Logs Captured

During exploration, these ChatKit events were logged:
1. `app.init {}` - Initial app load
2. `startScreenPrompt.select {text: "..."}` - Starter prompt clicked
3. `history.open {}` - History panel opened
4. `history.close {}` - History panel closed
5. `newChat.create {}` - New chat created
6. `widget.action {widgetType, actionType, handler}` - Widget interaction
7. `composer.tool.select {toolId, source}` - Tool selected

These events help understand the user flow and what backend events to handle.

## Screenshots Captured

1. **chatkit-playground-overview.png** - Initial playground view
2. **chatkit-widgets-example.png** - Widget list demonstration
3. **chatkit-email-widget-opened.png** - Email widget expanded view
4. **chatkit-search-docs-tool.png** - Search docs tool activated

All screenshots saved to: `.playwright-mcp/`

## Production Considerations

1. **Security**:
   - Use strong `SESSION_SECRET_KEY` (not dev default)
   - Enable `https_only=True` for session cookies
   - Implement rate limiting on API endpoint
   - Validate all user inputs

2. **Performance**:
   - Consider database backend instead of MemoryStore
   - Implement caching for thread lists
   - Optimize SSE streaming for large responses

3. **Scalability**:
   - Move from in-memory to persistent storage (PostgreSQL/Redis)
   - Implement horizontal scaling with shared session store
   - Add health checks and monitoring

## Advanced Features to Consider

### 1. Widgets Support
- Define widget schemas in backend responses
- Handle widget actions (both client and server-side)
- Support widget state persistence

### 2. Client-Side Tools
- Implement tool configuration in frontend
- Handle tool activation/deactivation
- Support custom placeholder text per tool
- Process tool-specific user input

### 3. Message Actions
- Implement feedback (thumbs up/down) storage
- Support message regeneration
- Track user preferences

### 4. Thread Features
- Auto-generate thread titles from first message
- Support thread archiving/unarchiving
- Implement thread search functionality
- Add thread export capabilities

## References

- ChatKit Studio Playground: https://chatkit.studio/playground
- ChatKit Documentation: https://docs.chatkit.studio
- Our Implementation: `/Users/ckifonidis/projects/chatkit-langgraph-integration/`
- Screenshots: `.playwright-mcp/`
