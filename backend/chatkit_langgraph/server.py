"""
LangGraph ChatKit Server - Extensible adapter for LangGraph API with ChatKit.

This module provides a ChatKit server implementation that uses LangGraph API
for generating responses, with hooks for custom message handling.
"""

from __future__ import annotations

import logging
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, AsyncIterator
from uuid import uuid4

from chatkit.server import ChatKitServer, ThreadItemDoneEvent
from chatkit.types import (
    AssistantMessageContent,
    AssistantMessageItem,
    Attachment,
    ClientToolCallItem,
    Page,
    Thread,
    ThreadItem,
    ThreadMetadata,
    ThreadStreamEvent,
    ThreadUpdatedEvent,
    UserMessageItem,
    WidgetItem,
)
from openai.types.responses import ResponseInputContentParam

from .client import LangGraphStreamClient
from .store import MemoryStore

logger = logging.getLogger(__name__)


def _gen_id(prefix: str) -> str:
    """Generate a unique ID with a prefix."""
    return f"{prefix}_{uuid4().hex[:8]}"


def _user_message_text(item: UserMessageItem) -> str:
    """Extract text content from a user message item."""
    parts: list[str] = []
    for part in item.content:
        text = getattr(part, "text", None)
        if text:
            parts.append(text)
    return " ".join(parts).strip()


def _is_tool_completion_item(item: Any) -> bool:
    """Check if an item is a tool completion (client tool call)."""
    return isinstance(item, ClientToolCallItem)


def _transform_property_coordinates(properties: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Transform geoPoint string coordinates to GeoJSON format.

    LangGraph API returns: "geoPoint": "38.88867815432092,22.425554227711005"
    Frontend expects: "geoPoint": {"coordinates": [22.425554227711005, 38.88867815432092]}

    Args:
        properties: List of property dictionaries from LangGraph API

    Returns:
        List of properties with transformed coordinates
    """
    for prop in properties:
        try:
            address = prop.get("address")
            if not address or not isinstance(address, dict):
                continue

            geo_point = address.get("geoPoint")
            if not geo_point or not isinstance(geo_point, str):
                continue

            # Parse "latitude,longitude" string
            parts = geo_point.split(",")
            if len(parts) != 2:
                logger.warning(f"Invalid geoPoint format: {geo_point}")
                continue

            try:
                lat = float(parts[0].strip())
                lng = float(parts[1].strip())

                # Transform to GeoJSON format: [longitude, latitude]
                address["geoPoint"] = {
                    "type": "Point",
                    "coordinates": [lng, lat]
                }
                logger.debug(f"Transformed coordinates for property {prop.get('code', 'unknown')}: [{lng}, {lat}]")
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse coordinates '{geo_point}': {e}")
                continue

        except Exception as e:
            logger.error(f"Error transforming coordinates for property: {e}")
            continue

    return properties


class MessageHandler(ABC):
    """
    Abstract base class for custom message handlers.

    Implement this to add custom logic before LangGraph processing,
    such as widget triggers, special commands, or routing logic.
    """

    @abstractmethod
    async def should_handle(
        self,
        user_message: str,
        thread: ThreadMetadata,
        context: dict[str, Any]
    ) -> bool:
        """
        Determine if this handler should process the message.

        Args:
            user_message: The user's message text
            thread: ChatKit thread metadata
            context: Request context

        Returns:
            True if this handler should process the message
        """
        pass

    @abstractmethod
    async def handle(
        self,
        user_message: str,
        thread: ThreadMetadata,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Handle the message and yield ChatKit events.

        Args:
            user_message: The user's message text
            thread: ChatKit thread metadata
            context: Request context

        Yields:
            ChatKit thread stream events
        """
        pass


class LangGraphChatKitServer(ChatKitServer[dict[str, Any]]):
    """
    ChatKit server implementation using LangGraph API.

    This server:
    - Integrates LangGraph API with ChatKit protocol
    - Converts LangGraph streaming events to ChatKit format
    - Maintains conversation history via Store interface
    - Supports extensible message handlers for custom logic
    - Provides thread persistence across messages

    Example:
        ```python
        server = LangGraphChatKitServer(
            langgraph_url="https://your-api.com",
            assistant_id="your-assistant",
            message_handlers=[CustomWidgetHandler()]
        )
        ```
    """

    def __init__(
        self,
        langgraph_url: str,
        assistant_id: str,
        store: MemoryStore | None = None,
        message_handlers: list[MessageHandler] | None = None,
        component_registry: Any | None = None,
        timeout: float = 60.0,
    ) -> None:
        """
        Initialize the LangGraph ChatKit server.

        Args:
            langgraph_url: Base URL of LangGraph API (required)
            assistant_id: LangGraph assistant/graph ID (required)
            store: ChatKit store implementation (defaults to MemoryStore)
            message_handlers: List of custom message handlers (optional)
            component_registry: ComponentRegistry for rule-based widgets (optional)
            timeout: Request timeout in seconds (default: 60.0)

        Raises:
            ValueError: If langgraph_url or assistant_id is not provided
        """
        if not langgraph_url:
            raise ValueError("langgraph_url is required")
        if not assistant_id:
            raise ValueError("assistant_id is required")

        self.store = store or MemoryStore()
        super().__init__(self.store)

        self.langgraph_url = langgraph_url
        self.assistant_id = assistant_id
        self.message_handlers = message_handlers or []
        self.component_registry = component_registry
        self.timeout = timeout

        # Initialize LangGraph client
        self.langgraph_client = LangGraphStreamClient(
            base_url=self.langgraph_url,
            assistant_id=self.assistant_id,
            timeout=self.timeout,
        )

        # Map ChatKit thread IDs to LangGraph UUIDs
        self._thread_id_map: dict[str, str] = {}

        logger.info(f"LangGraph ChatKit Server initialized: {self.langgraph_url}")

    def _to_thread_response(self, thread: ThreadMetadata | Thread) -> Thread:
        """
        Convert ThreadMetadata to Thread for ThreadUpdatedEvent emission.

        Follows the official ChatKit SDK pattern. Thread objects are required
        for ThreadUpdatedEvent, but respond() receives ThreadMetadata.

        This mirrors the implementation in chatkit.server.ChatKitServer._to_thread_response()
        and ensures proper type conversion for event emission.

        Args:
            thread: ThreadMetadata from respond() or Thread

        Returns:
            Thread object with empty items page (items managed separately)
        """
        # If already Thread, use its items; otherwise empty Page
        items = thread.items if isinstance(thread, Thread) else Page()

        # Construct Thread from metadata fields
        return Thread(
            id=thread.id,
            title=thread.title,
            created_at=thread.created_at,
            items=items,
            status=thread.status,
            metadata=thread.metadata,
        )

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Generate a response using LangGraph API or custom handlers.

        This method:
        1. Checks custom message handlers first
        2. Falls back to LangGraph API if no handler claims the message
        3. Streams response from LangGraph API
        4. Converts final response to ChatKit format
        5. Yields ChatKit stream events

        Args:
            thread: ChatKit thread metadata
            item: User message item (or None for retry)
            context: Request context (includes user_id)

        Yields:
            ChatKit thread stream events
        """
        # Handle missing or tool completion items
        target_item: ThreadItem | None = item
        if target_item is None:
            target_item = await self._latest_thread_item(thread, context)

        if target_item is None or _is_tool_completion_item(target_item):
            return

        # Extract user message text
        if not isinstance(target_item, UserMessageItem):
            logger.warning(f"Unexpected item type: {type(target_item)}")
            return

        user_message = _user_message_text(target_item)
        if not user_message:
            logger.warning("Empty user message")
            return

        print(f"[DEBUG] Message: thread={thread.id}, user={context.get('user_id', 'anon')[:8]}, msg={user_message[:50]}")

        # Check custom message handlers first
        for handler in self.message_handlers:
            if await handler.should_handle(user_message, thread, context):
                logger.info(f"Message handled by {handler.__class__.__name__}")
                async for event in handler.handle(user_message, thread, context):
                    yield event
                return

        # No custom handler claimed the message, use LangGraph
        async for event in self._handle_with_langgraph(
            user_message, thread, context
        ):
            yield event

    async def _handle_with_langgraph(
        self,
        user_message: str,
        thread: ThreadMetadata,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Handle message using LangGraph API.

        Args:
            user_message: User's message text
            thread: ChatKit thread metadata
            context: Request context

        Yields:
            ChatKit thread stream events
        """
        # Load thread-specific user preferences from store
        user_id = context.get("user_id", "anonymous")
        thread_id = thread.id  # ChatKit thread ID
        user_preferences = self.store.get_preferences(user_id, thread_id)
        print(f"[DEBUG] Thread-specific preferences loaded for thread={thread_id}: favorites={len(user_preferences.get('favorites', []))}, hidden={len(user_preferences.get('hidden', []))}")

        # Map ChatKit thread ID to LangGraph UUID
        # Simple: if mapping exists, reuse it; otherwise create new UUID
        langgraph_thread_id = self._thread_id_map.setdefault(thread.id, str(uuid4()))
        print(f"[DEBUG] Thread mapping: {thread.id} -> {langgraph_thread_id}")

        # Buffer to collect final response
        final_ai_message: dict[str, Any] | None = None
        final_event: dict[str, Any] | None = None

        try:
            # Stream from LangGraph API
            event_count = 0
            async for event in self.langgraph_client.stream_response(
                thread_id=langgraph_thread_id,
                user_message=user_message,
            ):
                event_count += 1

                # Skip metadata events
                if self.langgraph_client.get_metadata_event(event):
                    continue

                # Buffer the full event for component processing
                # Always process ALL events - the last one has the most complete data
                final_event = event
                print(f"[DEBUG] Event #{event_count} keys: {list(event.keys())[:5]}")

                # Extract AI message only if it appears after the latest human message
                ai_msg = self.langgraph_client.extract_ai_message_after_last_human(event)
                if ai_msg:
                    final_ai_message = ai_msg
                    print(f"[DEBUG] Found NEW AI message (after latest human) in event #{event_count}")

                # Don't break early - process all events until stream ends naturally

            print(f"[DEBUG] Processed {event_count} events total")

            # Check if we have query results (property search response)
            has_query_results = final_event and len(final_event.get("query_results", [])) > 0

            # Transform property coordinates from string to GeoJSON format
            if has_query_results and final_event:
                query_results = final_event.get("query_results", [])
                _transform_property_coordinates(query_results)
                print(f"[DEBUG] Transformed coordinates for {len(query_results)} properties")

            # Handle response based on what we received
            if final_ai_message:
                ai_content = final_ai_message.get("content", "")

                if not ai_content:
                    logger.warning("Empty AI response content")
                    ai_content = "I'm sorry, I couldn't generate a response."

                # Create assistant message item
                ai_message_id = _gen_id("msg")
                ai_message_item = AssistantMessageItem(
                    id=ai_message_id,
                    thread_id=thread.id,
                    created_at=datetime.now(),
                    content=[AssistantMessageContent(text=ai_content)],
                    status="completed",
                )

                # Yield the completed message as a done event
                yield ThreadItemDoneEvent(item=ai_message_item)
                print(f"[DEBUG] AI response: {len(ai_content)} chars")

                # Check component registry for additional widgets to render
                if self.component_registry and final_event:
                    print(f"[DEBUG] Checking components. Event keys: {list(final_event.keys())}")
                    print(f"[DEBUG] Has query_results: {'query_results' in final_event}, count: {len(final_event.get('query_results', []))}")
                    # Add user query to response_data for components
                    response_data_with_query = {**final_event, "_user_query": user_message}
                    widgets = self.component_registry.get_widgets(response_data_with_query, user_preferences=user_preferences)
                    print(f"[DEBUG] Component registry returned {len(widgets)} widgets")

                    # Separate widgets: Card widgets (FiltersCard) vs ListView widgets (PropertyCarousel)
                    from chatkit.widgets import Card, ListView
                    card_widgets = []
                    other_widgets = []

                    for widget in widgets:
                        if isinstance(widget, Card):
                            card_widgets.append(widget)
                        else:
                            other_widgets.append(widget)

                    # Yield Card widgets first (FiltersCard)
                    for widget in card_widgets:
                        widget_id = _gen_id("widget")
                        widget_item = WidgetItem(
                            id=widget_id,
                            thread_id=thread.id,
                            created_at=datetime.now(),
                            widget=widget,
                            status="completed",
                        )
                        yield ThreadItemDoneEvent(item=widget_item)
                        print(f"[DEBUG] Yielded Card widget")

                # Add property count message AFTER Card widgets, BEFORE ListView (if we have query results)
                if has_query_results:
                    total_count = final_event.get("results_count", len(query_results))
                    showing_count = len(query_results)

                    count_text = f"Showing {showing_count} of {total_count} properties"

                    count_msg_id = _gen_id("msg")
                    count_item = AssistantMessageItem(
                        id=count_msg_id,
                        thread_id=thread.id,
                        created_at=datetime.now(),
                        content=[AssistantMessageContent(text=count_text)],
                        status="completed",
                    )
                    yield ThreadItemDoneEvent(item=count_item)
                    print(f"[DEBUG] Showing {showing_count} of {total_count} properties")

                # Yield remaining widgets (PropertyCarousel ListView)
                if self.component_registry and final_event:
                    for widget in other_widgets:
                        widget_id = _gen_id("widget")
                        widget_item = WidgetItem(
                            id=widget_id,
                            thread_id=thread.id,
                            created_at=datetime.now(),
                            widget=widget,
                            status="completed",
                        )
                        yield ThreadItemDoneEvent(item=widget_item)
                        print(f"[DEBUG] Yielded ListView/other widget")

            elif has_query_results:
                # No AI message but we have query results
                # Check component registry for widgets
                if self.component_registry and final_event:
                    print(f"[DEBUG] Checking components for query results")
                    # Add user query to response_data for components
                    response_data_with_query = {**final_event, "_user_query": user_message}
                    widgets = self.component_registry.get_widgets(response_data_with_query, user_preferences=user_preferences)
                    print(f"[DEBUG] Component registry returned {len(widgets)} widgets")

                    # Separate widgets: Card widgets (FiltersCard) vs ListView widgets (PropertyCarousel)
                    from chatkit.widgets import Card, ListView
                    card_widgets = []
                    other_widgets = []

                    for widget in widgets:
                        if isinstance(widget, Card):
                            card_widgets.append(widget)
                        else:
                            other_widgets.append(widget)

                    # Yield Card widgets first (FiltersCard)
                    for widget in card_widgets:
                        widget_id = _gen_id("widget")
                        widget_item = WidgetItem(
                            id=widget_id,
                            thread_id=thread.id,
                            created_at=datetime.now(),
                            widget=widget,
                            status="completed",
                        )
                        yield ThreadItemDoneEvent(item=widget_item)
                        print(f"[DEBUG] Yielded Card widget")

                # Add property count message AFTER Card widgets, BEFORE ListView
                total_count = final_event.get("results_count", len(final_event.get("query_results", [])))
                showing_count = len(final_event.get("query_results", []))

                intro_text = f"Showing {showing_count} of {total_count} properties"

                intro_msg_id = _gen_id("msg")
                intro_item = AssistantMessageItem(
                    id=intro_msg_id,
                    thread_id=thread.id,
                    created_at=datetime.now(),
                    content=[AssistantMessageContent(text=intro_text)],
                    status="completed",
                )
                yield ThreadItemDoneEvent(item=intro_item)
                print(f"[DEBUG] Query results without AI message, showing {showing_count} of {total_count} results")

                # Yield remaining widgets (PropertyCarousel ListView)
                if self.component_registry and final_event:
                    for widget in other_widgets:
                        widget_id = _gen_id("widget")
                        widget_item = WidgetItem(
                            id=widget_id,
                            thread_id=thread.id,
                            created_at=datetime.now(),
                            widget=widget,
                            status="completed",
                        )
                        yield ThreadItemDoneEvent(item=widget_item)
                        print(f"[DEBUG] Yielded ListView/other widget")

            else:
                logger.warning("No AI message or query results found")
                # Yield error message
                error_msg_id = _gen_id("msg")
                error_item = AssistantMessageItem(
                    id=error_msg_id,
                    thread_id=thread.id,
                    created_at=datetime.now(),
                    content=[
                        AssistantMessageContent(
                            text="I apologize, but I encountered an issue generating a response. Please try again."
                        )
                    ],
                    status="completed",
                )
                yield ThreadItemDoneEvent(item=error_item)

            # Update thread title
            print(f"[THREAD-TITLE] Starting title update check")
            print(f"[THREAD-TITLE] Thread type: {type(thread)}")
            print(f"[THREAD-TITLE] Thread ID: {thread.id}")
            print(f"[THREAD-TITLE] Current title: {thread.title}")

            filters_summary = final_event.get("filters_summary")
            print(f"[THREAD-TITLE] filters_summary from response: {filters_summary}")

            if filters_summary:
                print(f"[THREAD-TITLE] Found filters_summary: '{filters_summary}'")
                print(f"[THREAD-TITLE] Setting new title: '{filters_summary[:60].strip()}')")
                # Use filters_summary from LangGraph
                thread.title = filters_summary[:60].strip()

                # Save updated thread
                await self.store.save_thread(thread, context)

                # Notify frontend of title change
                print(f"[THREAD-TITLE] About to yield ThreadUpdatedEvent (filters_summary path)")
                print(f"[THREAD-TITLE] Thread for event - type: {type(thread).__name__}, id: {thread.id}, title: {thread.title}")
                try:
                    # Use ChatKit SDK official pattern for ThreadMetadata → Thread conversion
                    yield ThreadUpdatedEvent(thread=self._to_thread_response(thread))
                    print(f"[THREAD-TITLE] Successfully yielded ThreadUpdatedEvent")
                except Exception as e:
                    print(f"[THREAD-TITLE] ERROR yielding ThreadUpdatedEvent: {e}")
                    logger.error(f"[THREAD-TITLE] Full error:", exc_info=True)
                    print(f"[THREAD-TITLE] Thread dump: {thread.model_dump()}")
                    raise

            elif thread.title is None and user_message:
                print(f"[THREAD-TITLE] Using fallback title from user message")
                print(f"[THREAD-TITLE] User message (first 50 chars): '{user_message[:50]}'")
                # Fallback: Use first message if title is not set yet
                thread.title = user_message[:50].strip()
                if len(user_message) > 50:
                    thread.title += "..."

                print(f"[THREAD-TITLE] Fallback title set to: '{thread.title}'")

                # Save updated thread
                await self.store.save_thread(thread, context)

                # Notify frontend of title change
                print(f"[THREAD-TITLE] About to yield ThreadUpdatedEvent (fallback path)")
                print(f"[THREAD-TITLE] Thread for event - type: {type(thread).__name__}, id: {thread.id}, title: {thread.title}")
                try:
                    # Use ChatKit SDK official pattern for ThreadMetadata → Thread conversion
                    yield ThreadUpdatedEvent(thread=self._to_thread_response(thread))
                    print(f"[THREAD-TITLE] Successfully yielded ThreadUpdatedEvent (fallback)")
                except Exception as e:
                    print(f"[THREAD-TITLE] ERROR yielding ThreadUpdatedEvent (fallback): {e}")
                    logger.error(f"[THREAD-TITLE] Full error:", exc_info=True)
                    print(f"[THREAD-TITLE] Thread dump: {thread.model_dump()}")
                    raise

        except Exception as e:
            logger.error(
                f"Error streaming from LangGraph",
                extra={"error": str(e), "thread_id": thread.id},
            )

            # Yield error message to user
            error_msg_id = _gen_id("msg")
            error_item = AssistantMessageItem(
                id=error_msg_id,
                thread_id=thread.id,
                created_at=datetime.now(),
                content=[
                    AssistantMessageContent(
                        text=f"I'm sorry, I encountered an error: {str(e)}. Please try again."
                    )
                ],
                status="completed",
            )
            yield ThreadItemDoneEvent(item=error_item)

    async def action(
        self,
        thread: ThreadMetadata,
        action: Any,
        sender: WidgetItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Handle widget actions.

        This method is called when a user interacts with a widget
        (e.g., clicks a button or carousel item).

        Args:
            thread: ChatKit thread metadata
            action: Action object with type and payload
            sender: The widget item that sent the action
            context: Request context

        Yields:
            ChatKit thread stream events (none for preference updates)
        """
        logger.info(
            f"Handling action: {action.type}",
            extra={"thread_id": thread.id, "action_type": action.type},
        )

        # Ensure this is recognized as an async generator
        if False:
            yield  # type: ignore

        # Get user ID and thread ID from context
        user_id = context.get("user_id", "anonymous")
        thread_id = thread.id  # ChatKit thread ID

        # Handle toggle_favorite action
        if action.type == "toggle_favorite":
            property_code = action.payload.get("propertyCode")
            property_data = action.payload.get("item_data", {})
            if property_code and property_data:
                # Update thread-specific preferences silently (no immediate re-render)
                prefs = self.store.get_preferences(user_id, thread_id)
                if property_code in prefs['favorites']:
                    self.store.remove_favorite(user_id, property_code, thread_id)
                    logger.info(f"Removed {property_code} from favorites for user {user_id[:8]} in thread {thread_id}")
                else:
                    self.store.add_favorite(user_id, property_code, property_data, thread_id)
                    logger.info(f"Added {property_code} to favorites for user {user_id[:8]} in thread {thread_id}")

                # Preferences will be used on next search/query in this thread
                print(f"[DEBUG] Updated thread preferences: {len(self.store.get_preferences(user_id, thread_id).get('favorites', {}))} favorites")

        # Handle hide_property action
        elif action.type == "hide_property":
            property_code = action.payload.get("propertyCode")
            property_data = action.payload.get("item_data", {})
            if property_code and property_data:
                # Update thread-specific preferences silently (no immediate re-render)
                self.store.hide_property(user_id, property_code, property_data, thread_id)
                logger.info(f"Hidden property {property_code} for user {user_id[:8]} in thread {thread_id}")

                # Preferences will be used on next search/query in this thread
                print(f"[DEBUG] Updated thread preferences: {len(self.store.get_preferences(user_id, thread_id).get('hidden', {}))} hidden")

    async def to_message_content(
        self, _input: Attachment
    ) -> ResponseInputContentParam:
        """
        Convert file attachments to message content.

        Note: Override this method to add file attachment support.
        """
        raise RuntimeError(
            "File attachments are not supported by default. "
            "Override to_message_content() to add attachment support."
        )

    async def _latest_thread_item(
        self, thread: ThreadMetadata, context: dict[str, Any]
    ) -> ThreadItem | None:
        """Get the latest item from a thread."""
        try:
            items = await self.store.load_thread_items(
                thread.id, None, 1, "desc", context
            )
        except Exception:  # pragma: no cover - defensive
            return None

        return items.data[0] if getattr(items, "data", None) else None


def create_server_from_env(
    store: MemoryStore | None = None,
    message_handlers: list[MessageHandler] | None = None,
    component_registry: Any | None = None,
) -> LangGraphChatKitServer:
    """
    Create a LangGraph ChatKit server from environment variables.

    Reads configuration from:
    - LANGGRAPH_API_URL: LangGraph API base URL
    - LANGGRAPH_ASSISTANT_ID: LangGraph assistant/graph ID
    - LANGGRAPH_TIMEOUT: Request timeout (optional, default: 60.0)

    Args:
        store: ChatKit store implementation (defaults to MemoryStore)
        message_handlers: List of custom message handlers (optional)
        component_registry: ComponentRegistry for rule-based widgets (optional)

    Returns:
        Configured LangGraphChatKitServer instance

    Raises:
        ValueError: If required environment variables are missing
    """
    langgraph_url = os.getenv("LANGGRAPH_API_URL")
    assistant_id = os.getenv("LANGGRAPH_ASSISTANT_ID")
    timeout = float(os.getenv("LANGGRAPH_TIMEOUT", "60.0"))

    if not langgraph_url:
        raise ValueError("LANGGRAPH_API_URL environment variable is required")
    if not assistant_id:
        raise ValueError("LANGGRAPH_ASSISTANT_ID environment variable is required")

    return LangGraphChatKitServer(
        langgraph_url=langgraph_url,
        assistant_id=assistant_id,
        store=store,
        message_handlers=message_handlers,
        component_registry=component_registry,
        timeout=timeout,
    )
