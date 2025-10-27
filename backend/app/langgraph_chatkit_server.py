"""
LangGraph ChatKit Server - Adapter for integrating LangGraph API with ChatKit.

This module provides a ChatKit server implementation that uses LangGraph API
instead of OpenAI Agents SDK for generating responses.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from typing import Any, AsyncIterator
from uuid import uuid4

from chatkit.server import ChatKitServer, ThreadItemDoneEvent
from chatkit.types import (
    AssistantMessageContent,
    AssistantMessageItem,
    Attachment,
    ClientToolCallItem,
    ThreadItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
    WidgetItem,
)
from openai.types.responses import ResponseInputContentParam

from .langgraph_client import LangGraphStreamClient
from .memory_store import MemoryStore
from .widget_examples import get_example_widget

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


class LangGraphChatKitServer(ChatKitServer[dict[str, Any]]):
    """
    ChatKit server implementation using LangGraph API.

    This server:
    - Replaces OpenAI Agents SDK with LangGraph API calls
    - Converts LangGraph streaming events to ChatKit format
    - Maintains conversation history in MemoryStore
    - Supports thread persistence across messages
    """

    def __init__(
        self,
        langgraph_url: str | None = None,
        assistant_id: str | None = None,
    ) -> None:
        """
        Initialize the LangGraph ChatKit server.

        Args:
            langgraph_url: Base URL of LangGraph API (or from LANGGRAPH_API_URL env var)
            assistant_id: LangGraph assistant/graph ID (or from LANGGRAPH_ASSISTANT_ID env var)
        """
        self.store: MemoryStore = MemoryStore()
        super().__init__(self.store)

        # Get configuration from environment or parameters
        self.langgraph_url = langgraph_url or os.getenv(
            "LANGGRAPH_API_URL",
            "https://nbg-webapp-cc-lg-test-we-dev-01-axhqfbexe3eeerbn.westeurope-01.azurewebsites.net",
        )
        self.assistant_id = assistant_id or os.getenv("LANGGRAPH_ASSISTANT_ID", "agent")

        # Initialize LangGraph client
        self.langgraph_client = LangGraphStreamClient(
            base_url=self.langgraph_url,
            assistant_id=self.assistant_id,
        )

        logger.info(
            f"Initialized LangGraph ChatKit Server",
            extra={
                "langgraph_url": self.langgraph_url,
                "assistant_id": self.assistant_id,
            },
        )

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict[str, Any],
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Generate a response using LangGraph API.

        This method:
        1. Extracts user message from ChatKit item
        2. Streams response from LangGraph API
        3. Buffers events until final AI response
        4. Converts final response to ChatKit format
        5. Yields ChatKit stream events

        Args:
            thread: ChatKit thread metadata
            item: User message item (or None for retry)
            context: Request context

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

        logger.info(
            f"Processing message for thread {thread.id}",
            extra={"message_preview": user_message[:100]},
        )

        # Check for carousel trigger keywords
        user_message_lower = user_message.lower()
        if "carousel" in user_message_lower or "show products" in user_message_lower or "show me products" in user_message_lower:
            # Yield intro text message
            intro_msg_id = _gen_id("msg")
            intro_item = AssistantMessageItem(
                id=intro_msg_id,
                thread_id=thread.id,
                created_at=datetime.now(),
                content=[AssistantMessageContent(
                    text="Here are some featured items for you to explore:"
                )],
                status="completed",
            )
            yield ThreadItemDoneEvent(item=intro_item)

            # Yield the carousel widget
            carousel_widget = get_example_widget("products")
            widget_id = _gen_id("widget")
            widget_item = WidgetItem(
                id=widget_id,
                thread_id=thread.id,
                created_at=datetime.now(),
                widget=carousel_widget,
                status="completed",
            )
            yield ThreadItemDoneEvent(item=widget_item)

            logger.info(f"Yielded carousel widget for thread {thread.id}")
            return

        # Validate thread ID format for LangGraph (must be UUID)
        langgraph_thread_id = thread.id
        try:
            # Try to parse as UUID to validate format
            uuid.UUID(thread.id)
        except ValueError:
            # If not a valid UUID, generate a new one
            # This can happen with ChatKit's default thread IDs
            langgraph_thread_id = str(uuid4())
            logger.info(
                f"Generated new UUID for LangGraph thread",
                extra={"chatkit_thread_id": thread.id, "langgraph_thread_id": langgraph_thread_id},
            )

        # Buffer to collect final response
        final_ai_message: dict[str, Any] | None = None

        try:
            # Stream from LangGraph API
            async for event in self.langgraph_client.stream_response(
                thread_id=langgraph_thread_id,
                user_message=user_message,
            ):
                # Skip metadata events
                if self.langgraph_client.get_metadata_event(event):
                    continue

                # Extract latest AI message
                ai_msg = self.langgraph_client.extract_latest_ai_message(event)
                if ai_msg:
                    final_ai_message = ai_msg

                # Check if this is the final response
                if self.langgraph_client.is_final_response(event):
                    logger.info("Final response detected")
                    break

            # If we have a final AI message, stream it as ChatKit events
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

                logger.info(
                    f"Yielded AI response",
                    extra={
                        "thread_id": thread.id,
                        "message_id": ai_message_id,
                        "content_length": len(ai_content),
                    },
                )
            else:
                logger.warning("No AI message found in LangGraph response")
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

        return

    async def to_message_content(self, _input: Attachment) -> ResponseInputContentParam:
        """
        Convert file attachments to message content.

        Note: File attachments are not supported in this demo.
        """
        raise RuntimeError("File attachments are not supported in this demo.")

    async def _latest_thread_item(
        self, thread: ThreadMetadata, context: dict[str, Any]
    ) -> ThreadItem | None:
        """Get the latest item from a thread."""
        try:
            items = await self.store.load_thread_items(thread.id, None, 1, "desc", context)
        except Exception:  # pragma: no cover - defensive
            return None

        return items.data[0] if getattr(items, "data", None) else None


def create_langgraph_chatkit_server(
    langgraph_url: str | None = None,
    assistant_id: str | None = None,
) -> LangGraphChatKitServer:
    """
    Factory function to create a LangGraph ChatKit server.

    Args:
        langgraph_url: Base URL of LangGraph API
        assistant_id: LangGraph assistant/graph ID

    Returns:
        Configured LangGraphChatKitServer instance
    """
    return LangGraphChatKitServer(
        langgraph_url=langgraph_url,
        assistant_id=assistant_id,
    )
