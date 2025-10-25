# LangGraph ChatKit Integration

This example demonstrates how to integrate ChatKit with a LangGraph API backend, replacing the OpenAI Agents SDK with your custom LangGraph deployment.

## What's Inside

- **FastAPI backend** that streams responses from a LangGraph API
- **ChatKit React UI** with conversation management
- **Thread persistence** using backend MemoryStore
- **Streaming support** for real-time AI responses
- **Greek language support** and multilingual conversations

## Architecture

```
User Message → ChatKit UI → FastAPI Backend → LangGraph API
                    ↑                              ↓
                    └──────── Streaming Response ──┘
```

### Key Components

**Backend** (`backend/app/`):
- `langgraph_chatkit_server.py` - Adapter that converts LangGraph events to ChatKit format
- `langgraph_client.py` - Client for streaming from LangGraph API
- `main.py` - FastAPI app with `/langgraph/chatkit` endpoint
- `memory_store.py` - Thread and message persistence

**Frontend** (`frontend/src/`):
- Standard ChatKit React components
- Configured to use `/langgraph/chatkit` endpoint
- Custom starter prompts for banking/assistant use cases

## Prerequisites

- Python 3.11+
- Node.js 18.18+, npm 9+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or `pip`
- Access to a LangGraph API endpoint

## Environment Variables

Required:
- `LANGGRAPH_API_URL` - Your LangGraph API base URL
- `LANGGRAPH_ASSISTANT_ID` - Assistant/graph ID (defaults to "agent")

## Quickstart

From the `examples/langgraph-integration` directory:

```bash
export LANGGRAPH_API_URL="https://your-langgraph-api.com"
npm start
```

This starts both backend (port 8004) and frontend (port 5174).

Open http://localhost:5174 in your browser.

## How It Works

1. User sends message through ChatKit UI
2. Backend calls LangGraph API with streaming
3. LangGraph events buffered until final AI response
4. Final response converted to ChatKit format
5. Response streamed back to UI in real-time

## Testing

Health check:
```bash
curl http://localhost:8004/langgraph/health
```

Try these prompts:
- "Hello, what can you help me with?"
- "Πες μου για τα δάνεια μου" (Greek)
- "Tell me about banking services"

## Learn More

- [ChatKit Documentation](https://docs.claude.com/en/docs/claude-code)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
