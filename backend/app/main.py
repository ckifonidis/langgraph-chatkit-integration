"""FastAPI entrypoint for LangGraph ChatKit integration."""

from __future__ import annotations

import os
from typing import Any

from chatkit.server import StreamingResult
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from chatkit_langgraph import LangGraphChatKitServer, create_server_from_env
from examples.carousel_handler import CarouselWidgetHandler

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

# Initialize the server with custom handlers
_langgraph_server: LangGraphChatKitServer | None = create_server_from_env(
    message_handlers=[
        CarouselWidgetHandler()  # Demo: Shows carousel when user asks for products
    ]
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


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "LangGraph ChatKit Integration API",
        "version": "0.1.0",
        "chatkit_endpoint": "/langgraph/chatkit",
        "health_endpoint": "/langgraph/health",
    }
