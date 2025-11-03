"""FastAPI entrypoint for LangGraph ChatKit integration."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Add backend directory to Python path for custom_components import
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from chatkit.server import StreamingResult
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from chatkit_langgraph import LangGraphChatKitServer, create_server_from_env
from custom_components import ComponentRegistry
from custom_components.property_carousel import PropertyCarouselComponent
from custom_components.save_search_button import SaveSearchButtonComponent

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
component_registry.register(SaveSearchButtonComponent())

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
    request: Request,
    server: LangGraphChatKitServer = Depends(get_langgraph_server),
) -> dict[str, Any]:
    """
    Get user preferences (favorites, hidden properties, and saved searches).

    Returns:
        Dictionary with favorites, hidden, saved_searches, and version
    """
    # Get or create user session ID
    if "user_id" not in request.session:
        import uuid
        request.session["user_id"] = str(uuid.uuid4())

    user_id = request.session["user_id"]
    preferences = server.store.get_preferences(user_id)

    return {
        "user_id": user_id[:8],  # Return truncated user_id for debugging
        "preferences": preferences,
    }


@app.post("/langgraph/preferences/favorites")
async def add_favorite(
    request: Request,
    server: LangGraphChatKitServer = Depends(get_langgraph_server),
) -> dict[str, Any]:
    """
    Add a property to user's favorites.

    Request body:
        {
            "propertyCode": "PROP001",
            "propertyData": { ... full property object ... }
        }

    Returns:
        Updated preferences
    """
    # Get user session ID
    if "user_id" not in request.session:
        return {"error": "No session found"}

    user_id = request.session["user_id"]

    # Get request body
    body = await request.json()
    property_code = body.get("propertyCode")
    property_data = body.get("propertyData", {})

    if not property_code or not property_data:
        return {"error": "propertyCode and propertyData are required"}

    # Add to favorites
    server.store.add_favorite(user_id, property_code, property_data)

    # Return updated preferences
    preferences = server.store.get_preferences(user_id)
    return {
        "success": True,
        "preferences": preferences,
    }


@app.delete("/langgraph/preferences/favorites/{property_code}")
async def remove_favorite(
    property_code: str,
    request: Request,
    server: LangGraphChatKitServer = Depends(get_langgraph_server),
) -> dict[str, Any]:
    """
    Remove a property from user's favorites.

    Args:
        property_code: Property code to remove

    Returns:
        Updated preferences
    """
    # Get user session ID
    if "user_id" not in request.session:
        return {"error": "No session found"}

    user_id = request.session["user_id"]

    # Remove from favorites
    server.store.remove_favorite(user_id, property_code)

    # Return updated preferences
    preferences = server.store.get_preferences(user_id)
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
    Hide a property.

    Request body:
        {
            "propertyCode": "PROP001",
            "propertyData": { ... full property object ... }
        }

    Returns:
        Updated preferences
    """
    # Get user session ID
    if "user_id" not in request.session:
        return {"error": "No session found"}

    user_id = request.session["user_id"]

    # Get request body
    body = await request.json()
    property_code = body.get("propertyCode")
    property_data = body.get("propertyData", {})

    if not property_code or not property_data:
        return {"error": "propertyCode and propertyData are required"}

    # Hide property
    server.store.hide_property(user_id, property_code, property_data)

    # Return updated preferences
    preferences = server.store.get_preferences(user_id)
    return {
        "success": True,
        "preferences": preferences,
    }


@app.delete("/langgraph/preferences/hidden/{property_code}")
async def unhide_property(
    property_code: str,
    request: Request,
    server: LangGraphChatKitServer = Depends(get_langgraph_server),
) -> dict[str, Any]:
    """
    Remove a property from user's hidden list (unhide it).

    Args:
        property_code: Property code to unhide

    Returns:
        Updated preferences
    """
    # Get user session ID
    if "user_id" not in request.session:
        return {"error": "No session found"}

    user_id = request.session["user_id"]

    # Unhide property
    server.store.unhide_property(user_id, property_code)

    # Return updated preferences
    preferences = server.store.get_preferences(user_id)
    return {
        "success": True,
        "preferences": preferences,
    }


@app.delete("/langgraph/preferences/saved-searches/{search_id}")
async def delete_saved_search_endpoint(
    search_id: str,
    request: Request,
    server: LangGraphChatKitServer = Depends(get_langgraph_server),
) -> dict[str, Any]:
    """
    Delete a saved search.

    Args:
        search_id: Saved search ID to delete

    Returns:
        Updated preferences
    """
    # Get user session ID
    if "user_id" not in request.session:
        return {"error": "No session found"}

    user_id = request.session["user_id"]

    # Delete saved search
    server.store.delete_saved_search(user_id, search_id)

    # Return updated preferences
    preferences = server.store.get_preferences(user_id)
    return {
        "success": True,
        "preferences": preferences,
    }


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "LangGraph ChatKit Integration API",
        "version": "0.1.0",
        "chatkit_endpoint": "/langgraph/chatkit",
        "health_endpoint": "/langgraph/health",
        "preferences_endpoint": "/langgraph/preferences",
    }
