"""FastAPI entrypoint for LangGraph ChatKit integration."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add backend directory to Python path for custom_components import
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from chatkit.server import StreamingResult
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from chatkit_langgraph import LangGraphChatKitServer, create_server_from_env
from chatkit_langgraph.description_client import DescriptionLangGraphClient
from custom_components import ComponentRegistry
from custom_components.property_carousel import PropertyCarouselComponent

logger = logging.getLogger(__name__)


class GenerateDescriptionRequest(BaseModel):
    """Request model for description generation."""

    propertyCode: str
    propertyData: dict[str, Any]
    language: str = "english"


app = FastAPI(title="LangGraph ChatKit Integration API")

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,  # Required for session cookies
)

# Add session middleware for user identification
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "dev-secret-key-change-in-production")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    session_cookie="chatkit_session",
    max_age=86400 * 30,  # 30 days
    same_site="lax",
    https_only=False,  # Set to True in production with HTTPS
)

# Initialize component registry with custom components
component_registry = ComponentRegistry()
component_registry.register(PropertyCarouselComponent(max_items=50))

# Initialize the server with custom components
_langgraph_server: LangGraphChatKitServer | None = create_server_from_env(
    message_handlers=[],
    component_registry=component_registry,
)


def get_langgraph_server() -> LangGraphChatKitServer:
    """Dependency injection for the LangGraph server."""
    if _langgraph_server is None:
        raise RuntimeError("LangGraph server not initialized")
    return _langgraph_server


@app.post("/langgraph/chatkit")
async def chatkit_endpoint(
    request: Request,
    server: LangGraphChatKitServer = Depends(get_langgraph_server),
) -> Response:
    """
    ChatKit endpoint that processes messages through LangGraph API.

    This endpoint:
    - Receives ChatKit protocol messages
    - Routes them to LangGraph API
    - Streams responses back in ChatKit format
    """
    # Get or create user session ID
    if "user_id" not in request.session:
        import uuid
        request.session["user_id"] = str(uuid.uuid4())

    user_id = request.session["user_id"]

    # Process the request with user context
    payload = await request.body()
    result = await server.process(
        payload,
        {
            "request": request,
            "user_id": user_id,
        },
    )

    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return JSONResponse(result)


@app.get("/langgraph/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    server = get_langgraph_server()
    return {
        "status": "healthy",
        "langgraph_url": server.langgraph_url,
        "assistant_id": server.assistant_id,
    }


@app.get("/langgraph/preferences")
async def get_preferences(
    thread_id: str,  # Required query parameter
    request: Request,
    server: LangGraphChatKitServer = Depends(get_langgraph_server),
) -> dict[str, Any]:
    """
    Get thread-specific user preferences (favorites, hidden properties).

    Args:
        thread_id: The ChatKit thread ID (required query parameter)

    Returns:
        Dictionary with favorites, hidden, and version for this thread
    """
    # Get or create user session ID
    if "user_id" not in request.session:
        import uuid
        request.session["user_id"] = str(uuid.uuid4())

    user_id = request.session["user_id"]
    preferences = server.store.get_preferences(user_id, thread_id)

    return {
        "user_id": user_id[:8],  # Return truncated user_id for debugging
        "thread_id": thread_id,
        "preferences": preferences,
    }


@app.post("/langgraph/preferences/favorites")
async def add_favorite(
    request: Request,
    server: LangGraphChatKitServer = Depends(get_langgraph_server),
) -> dict[str, Any]:
    """
    Add a property to thread-specific favorites.

    Request body:
        {
            "thread_id": "thr_abc123",
            "propertyCode": "PROP001",
            "propertyData": { ... full property object ... }
        }

    Returns:
        Updated preferences for this thread
    """
    # Get user session ID
    if "user_id" not in request.session:
        return {"error": "No session found"}

    user_id = request.session["user_id"]

    # Get request body
    body = await request.json()
    thread_id = body.get("thread_id")
    property_code = body.get("propertyCode")
    property_data = body.get("propertyData", {})

    if not thread_id or not property_code or not property_data:
        return {"error": "thread_id, propertyCode and propertyData are required"}

    # Add to thread-specific favorites
    server.store.add_favorite(user_id, property_code, property_data, thread_id)

    # Return updated preferences for this thread
    preferences = server.store.get_preferences(user_id, thread_id)
    return {
        "success": True,
        "preferences": preferences,
    }


@app.delete("/langgraph/preferences/favorites/{property_code}")
async def remove_favorite(
    property_code: str,
    thread_id: str,  # Required query parameter
    request: Request,
    server: LangGraphChatKitServer = Depends(get_langgraph_server),
) -> dict[str, Any]:
    """
    Remove a property from thread-specific favorites.

    Args:
        property_code: Property code to remove
        thread_id: The ChatKit thread ID (required query parameter)

    Returns:
        Updated preferences for this thread
    """
    # Get user session ID
    if "user_id" not in request.session:
        return {"error": "No session found"}

    user_id = request.session["user_id"]

    # Remove from thread-specific favorites
    server.store.remove_favorite(user_id, property_code, thread_id)

    # Return updated preferences for this thread
    preferences = server.store.get_preferences(user_id, thread_id)
    return {
        "success": True,
        "preferences": preferences,
    }


@app.post("/langgraph/preferences/hidden")
async def hide_property_endpoint(
    request: Request,
    server: LangGraphChatKitServer = Depends(get_langgraph_server),
) -> dict[str, Any]:
    """
    Hide a property in a specific thread.

    Request body:
        {
            "thread_id": "thr_abc123",
            "propertyCode": "PROP001",
            "propertyData": { ... full property object ... }
        }

    Returns:
        Updated preferences for this thread
    """
    # Get user session ID
    if "user_id" not in request.session:
        return {"error": "No session found"}

    user_id = request.session["user_id"]

    # Get request body
    body = await request.json()
    thread_id = body.get("thread_id")
    property_code = body.get("propertyCode")
    property_data = body.get("propertyData", {})

    if not thread_id or not property_code or not property_data:
        return {"error": "thread_id, propertyCode and propertyData are required"}

    # Hide property in this thread
    server.store.hide_property(user_id, property_code, property_data, thread_id)

    # Return updated preferences for this thread
    preferences = server.store.get_preferences(user_id, thread_id)
    return {
        "success": True,
        "preferences": preferences,
    }


@app.delete("/langgraph/preferences/hidden/{property_code}")
async def unhide_property(
    property_code: str,
    thread_id: str,  # Required query parameter
    request: Request,
    server: LangGraphChatKitServer = Depends(get_langgraph_server),
) -> dict[str, Any]:
    """
    Remove a property from thread-specific hidden list (unhide it).

    Args:
        property_code: Property code to unhide
        thread_id: The ChatKit thread ID (required query parameter)

    Returns:
        Updated preferences for this thread
    """
    # Get user session ID
    if "user_id" not in request.session:
        return {"error": "No session found"}

    user_id = request.session["user_id"]

    # Unhide property in this thread
    server.store.unhide_property(user_id, property_code, thread_id)

    # Return updated preferences for this thread
    preferences = server.store.get_preferences(user_id, thread_id)
    return {
        "success": True,
        "preferences": preferences,
    }


@app.post("/langgraph/generate-description")
async def generate_description(
    body: GenerateDescriptionRequest,
    request: Request,
    server: LangGraphChatKitServer = Depends(get_langgraph_server),
) -> dict[str, Any]:
    """
    Generate AI property description using the second LangGraph backend.

    This endpoint:
    - Checks global cache for existing description
    - If cached: returns immediately
    - If not cached: calls second LangGraph API and caches result

    Request body:
        {
            "propertyCode": "00000527",
            "propertyData": { ... full property object ... },
            "language": "english"  // optional, default: "english"
        }

    Returns:
        {
            "description": "Generated description text...",
            "cached": true/false,
            "propertyCode": "00000527"
        }
    """
    property_code = body.propertyCode
    property_data = body.propertyData
    language = body.language

    logger.info(f"Description requested for property {property_code} (language={language})")

    # Check global cache first
    cached_description = server.store.get_global_description(property_code)
    if cached_description:
        return {
            "description": cached_description,
            "cached": True,
            "propertyCode": property_code,
        }

    # Not cached - initialize description client and generate
    desc_api_url = os.getenv("LANGGRAPH_DESCRIPTION_API_URL")
    if not desc_api_url:
        logger.error("LANGGRAPH_DESCRIPTION_API_URL not configured")
        raise HTTPException(
            status_code=500,
            detail="Description service not configured. Please set LANGGRAPH_DESCRIPTION_API_URL.",
        )

    desc_assistant_id = os.getenv("LANGGRAPH_DESCRIPTION_ASSISTANT_ID", "agent")
    desc_timeout = int(os.getenv("LANGGRAPH_DESCRIPTION_TIMEOUT", "30"))

    desc_client = DescriptionLangGraphClient(
        base_url=desc_api_url,
        assistant_id=desc_assistant_id,
        timeout=desc_timeout,
    )

    try:
        # Generate description via second LangGraph API
        description = await desc_client.generate_description(
            property_data=property_data,
            language=language,
        )

        # Cache globally for all users
        server.store.cache_global_description(property_code, description)

        return {
            "description": description,
            "cached": False,
            "propertyCode": property_code,
        }

    except Exception as e:
        logger.error(
            f"Failed to generate description for property {property_code}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate description: {str(e)}",
        )


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "LangGraph ChatKit Integration API",
        "version": "0.1.0",
        "chatkit_endpoint": "/langgraph/chatkit",
        "health_endpoint": "/langgraph/health",
        "preferences_endpoint": "/langgraph/preferences",
        "generate_description_endpoint": "/langgraph/generate-description",
    }
