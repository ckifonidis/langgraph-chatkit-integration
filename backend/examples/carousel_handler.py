"""
Example: Carousel Widget Message Handler

This demonstrates how to create a custom MessageHandler that shows
a product carousel when the user asks for it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, AsyncIterator
from uuid import uuid4

from chatkit.server import ThreadItemDoneEvent
from chatkit.types import (
    AssistantMessageContent,
    AssistantMessageItem,
    ThreadMetadata,
    ThreadStreamEvent,
    WidgetItem,
)

from chatkit_langgraph import MessageHandler
from .widget_examples import get_example_widget


def _gen_id(prefix: str) -> str:
    """Generate a unique ID with a prefix."""
    return f"{prefix}_{uuid4().hex[:8]}"


class CarouselWidgetHandler(MessageHandler):
    """
    Message handler that triggers product carousel widgets.

    Example:
        ```python
        from chatkit_langgraph import LangGraphChatKitServer
        from examples.carousel_handler import CarouselWidgetHandler

        server = LangGraphChatKitServer(
            langgraph_url="...",
            assistant_id="...",
            message_handlers=[CarouselWidgetHandler()]
        )
        ```
    """

    def __init__(self, trigger_keywords: list[str] | None = None):
        """
        Initialize the carousel handler.

        Args:
            trigger_keywords: Keywords that trigger the carousel
                (default: ["carousel", "show products", "show me products"])
        """
        self.trigger_keywords = trigger_keywords or [
            "carousel",
            "show products",
            "show me products",
        ]

    async def should_handle(
        self, user_message: str, thread: ThreadMetadata, context: dict[str, Any]
    ) -> bool:
        """Check if message contains carousel trigger keywords."""
        user_message_lower = user_message.lower()
        return any(keyword in user_message_lower for keyword in self.trigger_keywords)

    async def handle(
        self, user_message: str, thread: ThreadMetadata, context: dict[str, Any]
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Handle carousel request by yielding intro text and widget.

        Args:
            user_message: The user's message text
            thread: ChatKit thread metadata
            context: Request context

        Yields:
            ChatKit thread stream events
        """
        # Yield intro text message
        intro_msg_id = _gen_id("msg")
        intro_item = AssistantMessageItem(
            id=intro_msg_id,
            thread_id=thread.id,
            created_at=datetime.now(),
            content=[
                AssistantMessageContent(
                    text="Here are some featured items for you to explore:"
                )
            ],
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
