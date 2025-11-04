"""
LangGraph API streaming client for ChatKit integration.

This module provides a reusable client for streaming responses from a LangGraph API
and converting them to ChatKit-compatible events.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator
from uuid import uuid4

import httpx
from chatkit.types import ThreadStreamEvent
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LangGraphMessage(BaseModel):
    """LangGraph message format."""

    content: str
    type: str  # "human" or "ai"
    id: str
    additional_kwargs: dict[str, Any] = Field(default_factory=dict)
    response_metadata: dict[str, Any] = Field(default_factory=dict)
    name: str | None = None
    example: bool = False
    tool_calls: list[Any] = Field(default_factory=list)
    invalid_tool_calls: list[Any] = Field(default_factory=list)
    usage_metadata: dict[str, Any] | None = None


class LangGraphStateEvent(BaseModel):
    """LangGraph state event containing the full state after each node."""

    messages: list[dict[str, Any]]
    queries: list[str] = Field(default_factory=list)
    retrieved_docs: list[dict[str, Any]] = Field(default_factory=list)
    routing_action: str | None = None
    routing_reasoning: str | None = None
    routing_confidence: float | None = None
    detected_handoff_tool: str | None = None
    tool_args: dict[str, Any] | None = None


class LangGraphMetadataEvent(BaseModel):
    """LangGraph metadata event at the start of a run."""

    run_id: str
    attempt: int


class LangGraphStreamClient:
    """
    Client for streaming responses from LangGraph API.

    This client handles:
    - Server-Sent Events (SSE) parsing
    - Thread creation with if_not_exists
    - State event stream processing
    - Conversation message extraction
    """

    def __init__(
        self,
        base_url: str,
        assistant_id: str = "agent",
        timeout: float = 60.0,
    ):
        """
        Initialize the LangGraph streaming client.

        Args:
            base_url: Base URL of the LangGraph API
            assistant_id: Assistant/graph ID to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.assistant_id = assistant_id
        self.timeout = timeout

    async def stream_response(
        self,
        thread_id: str | None,
        user_message: str,
        stream_mode: str = "values",
        if_not_exists: str = "create",
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Stream responses from the LangGraph API.

        Args:
            thread_id: Thread ID (will be generated if None)
            user_message: User's message content
            stream_mode: LangGraph stream mode (values, updates, messages, events)
            if_not_exists: What to do if thread doesn't exist (default: "create")

        Yields:
            Raw event dictionaries from the LangGraph stream
        """
        # Generate thread ID if not provided
        if thread_id is None:
            thread_id = str(uuid4())

        url = f"{self.base_url}/threads/{thread_id}/runs/stream"

        # Prepare request payload
        # Note: LangGraph expects "type": "human" not "role": "user"
        payload = {
            "input": {
                "messages": [{
                    "type": "human",
                    "content": user_message,
                    "id": str(uuid4()),  # Include message ID
                }]
            },
            "stream_mode": [stream_mode],
            "assistant_id": self.assistant_id,
        }

        if if_not_exists:
            payload["if_not_exists"] = if_not_exists

        print(f"[LANGGRAPH-REQUEST] ==================== NEW REQUEST ====================")
        print(f"[LANGGRAPH-REQUEST] URL: {url}")
        print(f"[LANGGRAPH-REQUEST] Thread ID: {thread_id}")
        print(f"[LANGGRAPH-REQUEST] User message: '{user_message}'")
        print(f"[LANGGRAPH-REQUEST] Full payload: {json.dumps(payload, indent=2)}")
        print(f"[LANGGRAPH-REQUEST] =====================================================")

        try:
            event_count = 0
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                    },
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(
                            f"LangGraph API error: {response.status_code}",
                            extra={"response": error_text.decode()},
                        )
                        raise Exception(
                            f"LangGraph API returned {response.status_code}: {error_text.decode()}"
                        )

                    # Parse Server-Sent Events (SSE)
                    async for line in response.aiter_lines():
                        # Skip empty lines and comments
                        if not line or line.startswith(":"):
                            continue

                        # Parse data lines
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix

                            try:
                                event_data = json.loads(data_str)
                                event_count += 1

                                # Log event (omit query_results to avoid huge logs)
                                event_for_logging = {k: v for k, v in event_data.items() if k != 'query_results'}
                                if 'query_results' in event_data:
                                    event_for_logging['query_results'] = f"[{len(event_data['query_results'])} items omitted]"

                                print(f"[LANGGRAPH-RESPONSE] Event #{event_count}: {json.dumps(event_for_logging, indent=2, default=str)}")

                                yield event_data

                            except json.JSONDecodeError as e:
                                logger.warning(
                                    f"JSON decode error in stream",
                                    extra={"error": str(e), "data": data_str[:200]},
                                )
                                continue

                        # Log event type lines for debugging
                        elif line.startswith("event: "):
                            event_type = line[7:]
                            logger.debug(f"Stream event type: {event_type}")

            print(f"[LANGGRAPH-RESPONSE] ==================== STREAM COMPLETE ====================")
            print(f"[LANGGRAPH-RESPONSE] Total events received: {event_count}")
            print(f"[LANGGRAPH-RESPONSE] ===========================================================")

        except httpx.RequestError as e:
            logger.error(f"LangGraph request error: {e}")
            raise
        except Exception as e:
            logger.error(f"LangGraph streaming error: {e}")
            raise

    def extract_latest_ai_message(
        self, state_event: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Extract the latest AI message from a state event.

        Args:
            state_event: LangGraph state event dictionary

        Returns:
            The latest AI message dict, or None if no AI messages exist
        """
        messages = state_event.get("messages", [])

        # Find the last AI message
        for msg in reversed(messages):
            if msg.get("type") == "ai":
                return msg

        return None

    def extract_full_conversation(
        self, state_event: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Extract all messages from a state event.

        Args:
            state_event: LangGraph state event dictionary

        Returns:
            List of all messages in chronological order
        """
        return state_event.get("messages", [])

    def get_metadata_event(self, event: dict[str, Any]) -> LangGraphMetadataEvent | None:
        """
        Parse a metadata event if this is one.

        Args:
            event: Raw event dictionary

        Returns:
            LangGraphMetadataEvent if this is a metadata event, None otherwise
        """
        if "run_id" in event and "attempt" in event and len(event.keys()) == 2:
            return LangGraphMetadataEvent(**event)
        return None

    def is_final_response(self, state_event: dict[str, Any]) -> bool:
        """
        Check if this state event contains a final response.

        A final response is indicated by:
        - At least one AI message exists
        - No pending actions (routing_action is None or completed)

        Args:
            state_event: LangGraph state event dictionary

        Returns:
            True if this appears to be a final response
        """
        # Check if there's an AI message
        ai_message = self.extract_latest_ai_message(state_event)
        if not ai_message:
            return False

        # Check if routing indicates completion
        routing_action = state_event.get("routing_action")

        # If routing_action is None or is a handoff (which completes the conversation)
        if routing_action is None or routing_action == "handoff":
            return True

        return False


# Convenience function
async def stream_langgraph(
    base_url: str,
    thread_id: str | None,
    user_message: str,
    assistant_id: str = "agent",
) -> AsyncIterator[dict[str, Any]]:
    """
    Convenience function to stream from LangGraph API.

    Args:
        base_url: LangGraph API base URL
        thread_id: Thread ID (generated if None)
        user_message: User's message
        assistant_id: Assistant ID to use

    Yields:
        State event dictionaries
    """
    client = LangGraphStreamClient(base_url=base_url, assistant_id=assistant_id)
    async for event in client.stream_response(thread_id, user_message):
        yield event
