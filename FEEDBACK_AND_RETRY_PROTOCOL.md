# ChatKit Feedback and Retry Protocol

## Overview
This document details how ChatKit handles message feedback (thumbs up/down) and message retry (regeneration) based on ChatKit Studio playground analysis.

## Console Events Captured

### Feedback Events

**Thumbs Up:**
```javascript
ChatKit log: message.action {action: feedback.positive}
```

**Thumbs Down:**
```javascript
ChatKit log: message.action {action: feedback.negative}
```

**Retry/Regenerate:**
```javascript
ChatKit log: message.action {action: retry}
```

## Network Behavior

After each action (thumbs up, thumbs down, retry), a POST request is sent to:
```
POST /chatkit
```

This suggests the feedback is sent via the ChatKit protocol, likely as a message type similar to `threads.list`.

## Expected Protocol Messages

### Feedback Message Format (Inferred)
```json
{
  "type": "items.feedback",
  "thread_id": "thr_abc123",
  "item_id": "msg_xyz789",
  "feedback": "positive"  // or "negative"
}
```

OR it could be:
```json
{
  "type": "items.update",
  "thread_id": "thr_abc123",
  "item_id": "msg_xyz789",
  "metadata": {
    "feedback": "positive"
  }
}
```

### Retry Message Format (Inferred)
```json
{
  "type": "items.retry",
  "thread_id": "thr_abc123",
  "item_id": "msg_xyz789"
}
```

OR it could reuse the respond mechanism:
```json
{
  "type": "messages.create",
  "thread_id": "thr_abc123",
  "retry": true,
  "item_id": "msg_xyz789"  // Message to regenerate after
}
```

## UI Behavior Observed

### Feedback Buttons
1. User clicks thumbs up → Button becomes disabled, event logged
2. User can then click thumbs down → Previous feedback is replaced
3. Buttons are mutually exclusive (can't have both active)
4. Visual state shows which feedback was given

### Retry Button
1. User clicks "Regenerate message"
2. Previous assistant message starts regenerating
3. Old message is replaced with new response
4. Streaming response appears in place

## Implementation Requirements

### Backend (Python)

#### Option 1: Handle as Metadata Update
```python
# In your ChatKit server implementation
async def handle_feedback(
    thread_id: str,
    item_id: str,
    feedback: str,  # "positive" or "negative"
    context: dict[str, Any]
) -> None:
    """Store feedback for a message."""
    item = await self.store.load_item(thread_id, item_id, context)

    # Update item metadata
    if not hasattr(item, 'metadata'):
        item.metadata = {}
    item.metadata['feedback'] = feedback
    item.metadata['feedback_timestamp'] = datetime.now().isoformat()

    await self.store.save_item(thread_id, item, context)
```

#### Option 2: Handle via ChatKit Protocol
```python
# The ChatKit library likely handles this automatically
# if you implement the Store interface correctly

# In MemoryStore, ensure save_item() supports metadata:
async def save_item(self, thread_id: str, item: ThreadItem, context: dict[str, Any]) -> None:
    items = self._items(thread_id)
    for idx, existing in enumerate(items):
        if existing.id == item.id:
            # Update existing item with new metadata
            items[idx] = item.model_copy(deep=True)
            return
    items.append(item.model_copy(deep=True))
```

### Frontend (TypeScript)

#### Enable Feedback in Configuration
```typescript
// In ChatKitPanel.tsx
const chatkit = useChatKit({
  // ... other config
  threadItemActions: {
    feedback: true,   // ← ENABLE THIS (currently false)
    retry: true       // ← ENABLE THIS (currently false)
  },
  // ... other config
});
```

#### Optional: Handle Feedback Events
```typescript
// If you want to track feedback events
onFeedback: (event) => {
  console.log('User gave feedback:', event);
  // event = {
  //   threadId: "thr_abc123",
  //   itemId: "msg_xyz789",
  //   feedback: "positive" | "negative"
  // }

  // Optional: Send to analytics
  analytics.track('message_feedback', event);
}
```

## Data Storage Strategy

### Thread Item with Feedback
```python
# Thread item structure
{
  "id": "msg_abc123",
  "thread_id": "thr_xyz789",
  "created_at": "2025-10-25T12:00:00",
  "content": [{"text": "ChatKit is..."}],
  "status": "completed",
  "metadata": {
    "feedback": "positive",  # or "negative", or null
    "feedback_timestamp": "2025-10-25T12:05:00",
    "user_id": "user_123"  # Track who gave feedback
  }
}
```

### Query Feedback Analytics
```python
# Example: Get positively rated messages
async def get_positive_feedback_messages(
    user_id: str,
    context: dict[str, Any]
) -> List[ThreadItem]:
    """Get all messages the user rated positively."""
    all_items = []
    for thread_id in self._user_threads.get(user_id, set()):
        items = await self.load_thread_items(thread_id, None, 9999, "desc", context)
        all_items.extend(items.data)

    return [
        item for item in all_items
        if item.metadata.get("feedback") == "positive"
    ]
```

## Retry/Regenerate Implementation

### How Retry Works
1. User clicks "Regenerate message"
2. Frontend sends retry request with the message ID to regenerate
3. Backend:
   - Retrieves the user message that preceded this assistant message
   - Calls LangGraph API again with same input
   - Generates new response
   - Replaces old assistant message with new one

### Backend Implementation
```python
# In LangGraphChatKitServer
async def retry_message(
    thread_id: str,
    item_id: str,  # The assistant message to regenerate
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
            # Get the previous item (should be user message)
            user_message_item = all_items.data[i - 1]
            break

    if not user_message_item:
        raise ValueError("Could not find user message to retry")

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

## Implementation Checklist

### Frontend Changes
- [ ] Enable feedback in `threadItemActions: { feedback: true }`
- [ ] Enable retry in `threadItemActions: { retry: true }`
- [ ] Optional: Add `onFeedback` callback for analytics
- [ ] Optional: Add `onRetry` callback for tracking

### Backend Changes
- [ ] Ensure `save_item()` in MemoryStore supports metadata updates
- [ ] Implement feedback storage (already supported via metadata)
- [ ] Implement retry/regenerate logic in ChatKitServer
- [ ] Add feedback query methods for analytics

### Testing
- [ ] Test thumbs up → verify metadata stored
- [ ] Test thumbs down → verify feedback replaced
- [ ] Test switching between thumbs up/down
- [ ] Test retry → verify new message generated
- [ ] Test retry preserves thread context

## Quick Implementation Guide

### Step 1: Enable in Frontend
```typescript
// frontend/src/components/ChatKitPanel.tsx
threadItemActions: {
  feedback: true,  // Change from false
  retry: true      // Change from false (if exists, or add it)
}
```

### Step 2: Verify Backend Support
The ChatKit library should automatically handle feedback via the Store interface. Our `MemoryStore.save_item()` already supports this!

### Step 3: Test
1. Start the app
2. Send a message
3. Click thumbs up → Check console for event
4. Check if metadata is stored in backend
5. Click retry → Verify new message generates

## Console Event Summary

| Action | Console Event |
|--------|---------------|
| Thumbs Up | `message.action {action: feedback.positive}` |
| Thumbs Down | `message.action {action: feedback.negative}` |
| Regenerate | `message.action {action: retry}` |

## Network Requests

All actions trigger:
```
POST /chatkit (with corresponding message type)
```

The ChatKit library abstracts the protocol, so we don't need to implement custom endpoints - just ensure our Store interface handles metadata correctly.

## Next Steps

1. **Enable feedback in frontend** (1 line change)
2. **Test feedback storage** (should work automatically)
3. **Implement retry logic** if ChatKit doesn't handle it automatically
4. **Add analytics** to track user satisfaction

## References
- Console logs from ChatKit Studio playground
- Network traffic analysis
- ChatKit documentation: https://docs.chatkit.studio
