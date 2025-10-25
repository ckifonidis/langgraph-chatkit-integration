#!/usr/bin/env python3
"""
End-to-end test of LangGraph ChatKit integration.
Tests the complete flow: ChatKit message -> LangGraph API -> ChatKit response
"""

import asyncio
import uuid

from app.langgraph_chatkit_server import LangGraphChatKitServer
from chatkit.types import ThreadMetadata, UserMessageItem, UserMessageTextContent
from datetime import datetime


async def test_langgraph_chatkit_integration():
    """Test the full integration flow."""
    print("=" * 80)
    print("End-to-End LangGraph ChatKit Integration Test")
    print("=" * 80)

    # Initialize server
    server = LangGraphChatKitServer()
    print(f"✅ Server initialized")
    print(f"   LangGraph URL: {server.langgraph_url}")
    print(f"   Assistant ID: {server.assistant_id}")
    print()

    # Create test thread
    thread_id = str(uuid.uuid4())
    thread = ThreadMetadata(id=thread_id, created_at=datetime.now())
    print(f"📝 Test Thread ID: {thread_id}")
    print()

    # Create test message
    user_message = UserMessageItem(
        id=f"msg_{uuid.uuid4().hex[:8]}",
        thread_id=thread_id,
        created_at=datetime.now(),
        content=[UserMessageTextContent(text="Hello! What can you help me with?")],
    )
    print(f"💬 Sending message: \"{user_message.content[0].text}\"")
    print("-" * 80)

    # Call the respond method
    event_count = 0
    final_response = None

    try:
        async for event in server.respond(
            thread=thread,
            item=user_message,
            context={"test": True},
        ):
            event_count += 1
            print(f"\n📨 Event #{event_count}: {type(event).__name__}")

            # Extract response content if it's a message
            if hasattr(event, "item") and hasattr(event.item, "content"):
                content = event.item.content
                if content and len(content) > 0:
                    text = getattr(content[0], "text", None)
                    if text:
                        final_response = text
                        print(f"   Content: {text[:200]}...")

        print("\n" + "=" * 80)
        print(f"✅ Test completed. Total events: {event_count}")

        if final_response:
            print(f"\n💬 Final AI Response:")
            print(f"{final_response}")
            print("\n✅ SUCCESS: LangGraph integration is working!")
        else:
            print("\n⚠️  WARNING: No response content found")

    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_langgraph_chatkit_integration())
